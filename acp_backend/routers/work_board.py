# acp_backend/routers/work_board.py
import logging
from typing import List 
from fastapi import APIRouter, HTTPException, Body, Path, Query, status, Depends

from acp_backend.config import settings
# Import INSTANCES from core for dependency providers
from acp_backend.core import fs_manager as global_fs_manager_instance
from acp_backend.core import session_handler as global_session_handler_instance
# Import CLASSES for type hinting
from acp_backend.core.fs_manager import FileSystemManager
from acp_backend.core.session_handler import SessionHandler

from acp_backend.models.work_board_models import (
    FileNode, ReadFileResponse, WriteFileRequest,
    CreateDirectoryRequest, MoveItemRequest
)

logger = logging.getLogger(__name__)
router = APIRouter()
MODULE_NAME = "WorkBoard Service"
TAG_WORKBOARD = "WorkBoard File System"

# Dependency provider functions
def get_fs_manager_dependency() -> FileSystemManager:
    if not global_fs_manager_instance: raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "File system service not initialized.")
    return global_fs_manager_instance

def get_session_handler_dependency() -> SessionHandler: # Already defined in work_sessions.py, ensure consistency or share
    if not global_session_handler_instance: raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Session service not initialized.")
    return global_session_handler_instance


async def _check_module_and_session(
    session_id: str, 
    current_session_handler: SessionHandler = Depends(get_session_handler_dependency) # Use injected handler
):
    if not settings.ENABLE_WORK_BOARD_MODULE:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"{MODULE_NAME} is currently disabled.")
    try:
        session = await current_session_handler.get_session(session_id) 
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid session ID format: {session_id}")
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session ID '{session_id}' not found.")

@router.get("/{session_id}/files", response_model=List[FileNode], summary="List Files and Directories", tags=[TAG_WORKBOARD], dependencies=[Depends(_check_module_and_session)])
async def list_files_in_work_board(
    session_id: str = Path(..., description="Session ID."),
    path: str = Query(".", description="Relative directory path."),
    current_fs_manager: FileSystemManager = Depends(get_fs_manager_dependency)
):
    try: return await current_fs_manager.list_dir(session_id, path)
    except FileNotFoundError as e: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NotADirectoryError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IOError as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {e}")
    except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {e}")

@router.get("/{session_id}/files/content", response_model=ReadFileResponse, summary="Read File Content", tags=[TAG_WORKBOARD], dependencies=[Depends(_check_module_and_session)])
async def read_file_content_from_work_board(
    session_id: str = Path(..., description="Session ID."),
    path: str = Query(..., description="Relative path of the file to read."),
    current_fs_manager: FileSystemManager = Depends(get_fs_manager_dependency)
):
    try: return await current_fs_manager.read_file(session_id, path)
    except FileNotFoundError as e: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IsADirectoryError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) # For decode errors
    except IOError as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {e}")
    except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {e}")

@router.post("/{session_id}/files/content", response_model=FileNode, status_code=status.HTTP_201_CREATED, summary="Write File Content", tags=[TAG_WORKBOARD], dependencies=[Depends(_check_module_and_session)])
async def write_file_content_to_work_board(
    session_id: str = Path(..., description="Session ID."),
    request: WriteFileRequest = Body(...),
    current_fs_manager: FileSystemManager = Depends(get_fs_manager_dependency)
):
    try: return await current_fs_manager.write_file(session_id, request)
    except FileNotFoundError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) # Path resolution
    except NotADirectoryError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IOError as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {e}")
    except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {e}")

@router.delete("/{session_id}/files", status_code=status.HTTP_204_NO_CONTENT, summary="Delete File or Directory", tags=[TAG_WORKBOARD], dependencies=[Depends(_check_module_and_session)])
async def delete_work_board_item(
    session_id: str = Path(..., description="Session ID."),
    path: str = Query(..., description="Relative path to delete."),
    current_fs_manager: FileSystemManager = Depends(get_fs_manager_dependency)
):
    try: 
        if not await current_fs_manager.delete_item(session_id, path):
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Deletion failed unexpectedly.")
    except FileNotFoundError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) # Path resolution
    except IOError as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {e}")
    except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {e}")
    return

@router.post("/{session_id}/directories", response_model=FileNode, status_code=status.HTTP_201_CREATED, summary="Create Directory", tags=[TAG_WORKBOARD], dependencies=[Depends(_check_module_and_session)])
async def create_work_board_directory(
    session_id: str = Path(..., description="Session ID."),
    request: CreateDirectoryRequest = Body(...),
    current_fs_manager: FileSystemManager = Depends(get_fs_manager_dependency)
):
    try: return await current_fs_manager.create_directory(session_id, request.path)
    except FileNotFoundError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except FileExistsError as e: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except IOError as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {e}")
    except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {e}")

@router.post("/{session_id}/move", response_model=FileNode, summary="Move/Rename File or Directory", tags=[TAG_WORKBOARD], dependencies=[Depends(_check_module_and_session)])
async def move_work_board_item(
    session_id: str = Path(..., description="Session ID."),
    request: MoveItemRequest = Body(...),
    current_fs_manager: FileSystemManager = Depends(get_fs_manager_dependency)
):
    try: return await current_fs_manager.move_item(session_id, request.source_path, request.destination_path)
    except FileNotFoundError as e: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) # Source not found
    except FileExistsError as e: raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) # Dest exists
    except NotADirectoryError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IOError as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {e}")
    except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {e}")
