"""
ACP Backend - Router for Interactive Terminal Service
"""
import logging
import asyncio
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path as FastApiPath, WebSocket, WebSocketDisconnect, status
import ptyprocess

from acp_backend.config import AppSettings
from acp_backend.core.session_handler import SessionHandler
from acp_backend.dependencies import get_app_settings, get_session_handler

logger = logging.getLogger(__name__)
router = APIRouter()
MODULE_NAME = "Interactive Terminal Service"
TAG_TERMINAL = "Terminal"

AppSettingsDep = Annotated[AppSettings, Depends(get_app_settings)]
SessionHandlerDep = Annotated[SessionHandler, Depends(get_session_handler)]

# Store active terminals (pty_process, task) - simple in-memory store
# In a multi-worker setup, this would need a more robust solution (e.g., Redis)
active_terminals: dict[str, tuple[ptyprocess.PtyProcess, asyncio.Task]] = {}

def _check_module_enabled(current_settings: AppSettingsDep):
    if not current_settings.ENABLE_TERMINAL_SERVICE_MODULE:
        logger.warning(f"{MODULE_NAME} is disabled in configuration.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{MODULE_NAME} is currently disabled.",
        )

@router.websocket("/sessions/{session_id}/ws")
async def terminal_websocket_endpoint(
    websocket: WebSocket,
    session_id: Annotated[str, FastApiPath(..., description="The ID of the workspace session")],
    settings: AppSettingsDep,
    session_handler: SessionHandlerDep,
    # token: Annotated[str | None, Cookie()] = None # Example for auth if needed
):
    _check_module_enabled(settings) # Ensure module is enabled before accepting websocket
    await websocket.accept()

    from uuid import UUID
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid session_id format.")
        return

    try:
        session_data_root = await session_handler.get_session_data_root(session_uuid)
        if not session_data_root.is_dir():
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=f"Session data directory not found for {session_id}")
            return
    except FileNotFoundError:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=f"Session {session_id} not found.")
        return
    except Exception as e:
        logger.error(f"Error getting session data root for {session_id}: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Server error preparing terminal.")
        return

    # Define the command to run (e.g., bash or system's default shell)
    # For security, ensure this is not user-configurable directly via API in a naive way
    shell_command = settings.DEFAULT_SHELL_COMMAND.split() 
    # Ensure DEFAULT_SHELL_COMMAND is in your AppSettings, e.g., DEFAULT_SHELL_COMMAND: str = "/bin/bash"
    
    cols, rows = 80, 24 # Default, can be updated via client message
    # Create a unique key for the terminal session (e.g., combining websocket id and session_id)
    # For simplicity, we'll use session_id, assuming one terminal per session for now.
    # A better key might be `f"{session_id}_{websocket.scope['client']}"` or a UUID
    term_key = session_id 

    if term_key in active_terminals:
        logger.warning(f"Terminal already active for session {session_id}. Closing new attempt.")
        # Potentially allow re-attaching or notify client
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Terminal already active for this session.")
        return

    try:
        logger.info(f"Starting PTY for session {session_id} in {session_data_root} with command: {shell_command}")
        pty_proc = ptyprocess.PtyProcess.spawn(
            shell_command,
            cwd=str(session_data_root),
            # env=os.environ, # Inherit environment, can be customized
            dimensions=(rows, cols)
        )
    except Exception as e:
        logger.error(f"Failed to spawn PTY for session {session_id}: {e}", exc_info=True)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Failed to start terminal process.")
        return

    async def forward_pty_output_to_websocket():
        try:
            while not pty_proc.closed:
                await asyncio.sleep(0.01) # Small sleep to prevent tight loop if no data
                try:
                    # Non-blocking read with timeout (ptyprocess uses select internally)
                    output = await asyncio.to_thread(pty_proc.read, 4096) # Read up to 4096 bytes
                    if output:
                        await websocket.send_text(output)
                except EOFError:
                    logger.info(f"PTY EOF for session {session_id}. Process likely exited.")
                    break
                except Exception as e:
                    logger.error(f"Error reading from PTY for session {session_id}: {e}", exc_info=True)
                    break # Exit loop on error
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected while forwarding PTY output for session {session_id}.")
        except Exception as e:
            logger.error(f"Unexpected error in forward_pty_output task for session {session_id}: {e}", exc_info=True)
        finally:
            logger.info(f"PTY output forwarding task finished for session {session_id}.")
            # Ensure PTY process is cleaned up if websocket closes or an error occurs here
            if not pty_proc.closed:
                pty_proc.close(force=True)
            if term_key in active_terminals:
                del active_terminals[term_key]
            # Attempt to close websocket if not already closed
            try:
                await websocket.close(code=status.WS_1001_GOING_AWAY, reason="Terminal session ended.")
            except RuntimeError: # Already closed
                pass

    output_task = asyncio.create_task(forward_pty_output_to_websocket())
    active_terminals[term_key] = (pty_proc, output_task)

    try:
        while True:
            data = await websocket.receive_text()
            # First byte might be a type indicator (e.g., for resize, data)
            # For a simple implementation, assume all data is input to the PTY
            # A more robust protocol would be: e.g., JSON messages for resize, data, etc.
            # Example: {"type": "resize", "cols": 120, "rows": 40} or {"type": "data", "payload": "ls -la\n"}
            
            # Basic resize handling (example, if client sends simple "resize:cols,rows")
            if data.startswith("resize:"):
                try:
                    _, dims = data.split(":", 1)
                    new_cols, new_rows = map(int, dims.split(","))
                    pty_proc.setwinsize(new_rows, new_cols)
                    logger.info(f"Resized PTY for session {session_id} to {new_rows}x{new_cols}")
                except Exception as e:
                    logger.warning(f"Failed to parse resize command for session {session_id}: {data}, error: {e}")
            else:
                 # Forward input from websocket to PTY
                pty_proc.write(data.encode())

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected by client for session {session_id}.")
    except Exception as e:
        logger.error(f"Error in main WebSocket loop for session {session_id}: {e}", exc_info=True)
        await websocket.close(code=status.WS_1011_INTERNAL_SERVER_ERROR, reason="Server error during terminal session.")
    finally:
        logger.info(f"Closing PTY and cleaning up for session {session_id}.")
        output_task.cancel() # Request cancellation of the output forwarding task
        try:
            await output_task # Wait for the task to actually cancel
        except asyncio.CancelledError:
            logger.info(f"Output task cancelled for session {session_id}")
        
        if not pty_proc.closed:
            pty_proc.close(force=True)
        
        if term_key in active_terminals:
            del active_terminals[term_key]
        logger.info(f"Terminal for session {session_id} fully cleaned up.") 