# acp_backend/routers/agents.py
import logging
import json 
import sys 
from typing import List, AsyncGenerator, Optional 
from fastapi import APIRouter, HTTPException, Body, Path, status, Depends
from sse_starlette.sse import EventSourceResponse

from acp_backend.config import settings, Settings
from acp_backend.core.agent_config_handler import AgentConfigHandler 
from acp_backend.core.agent_executor import AgentExecutor as AgentExecutorClass
from acp_backend.core.llm_manager import LLMManager

from acp_backend.dependencies import (
    get_agent_config_handler_dependency, 
    get_agent_executor_dependency, 
    get_llm_manager_dependency, 
    get_settings_dependency
)

from acp_backend.models.agent_models import (
    AgentConfig, RunAgentRequest, AgentRunStatus, AgentOutputChunk
)

logger = logging.getLogger(__name__)
router = APIRouter()
MODULE_NAME = "Agents Service"
TAG_AGENT_CONFIG_GLOBAL = "Agent Configuration (Global)"
TAG_AGENT_CONFIG_LOCAL = "Agent Configuration (Session-Scoped)"
TAG_AGENT_EXECUTION = "Agent Execution"


def _check_module_enabled(current_settings: Settings = Depends(get_settings_dependency)):
    if not current_settings.ENABLE_AGENT_MODULE:
        logger.warning(f"{MODULE_NAME} is disabled in configuration.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"{MODULE_NAME} is currently disabled.")

@router.post("/configs/global", response_model=AgentConfig, status_code=status.HTTP_201_CREATED, summary="Create Global Agent Configuration", tags=[TAG_AGENT_CONFIG_GLOBAL], dependencies=[Depends(_check_module_enabled)])
async def create_global_agent_configuration(config_payload: AgentConfig = Body(...), handler: AgentConfigHandler = Depends(get_agent_config_handler_dependency)): 
    try:
        if await handler.get_global_agent_config(config_payload.agent_id): raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Global agent ID '{config_payload.agent_id}' already exists.")
        await handler.save_global_agent_config(config_payload)
        persisted_config = await handler.get_global_agent_config(config_payload.agent_id)
        if not persisted_config: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve after saving.")
        return persisted_config
    except IOError as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {e}")
    except ValueError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/configs/global/{agent_id}", response_model=AgentConfig, summary="Get Global Agent Configuration", tags=[TAG_AGENT_CONFIG_GLOBAL], dependencies=[Depends(_check_module_enabled)])
async def get_global_agent_configuration(agent_id: str = Path(...), handler: AgentConfigHandler = Depends(get_agent_config_handler_dependency)): 
    try: config = await handler.get_global_agent_config(agent_id)
    except ValueError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not config: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Global agent ID '{agent_id}' not found.")
    return config

@router.get("/configs/global", response_model=List[AgentConfig], summary="List All Global Agent Configurations", tags=[TAG_AGENT_CONFIG_GLOBAL], dependencies=[Depends(_check_module_enabled)])
async def list_all_global_agent_configurations(handler: AgentConfigHandler = Depends(get_agent_config_handler_dependency)): 
    return await handler.list_global_agent_configs()

@router.put("/configs/global/{agent_id}", response_model=AgentConfig, summary="Update Global Agent Configuration", tags=[TAG_AGENT_CONFIG_GLOBAL], dependencies=[Depends(_check_module_enabled)])
async def update_global_agent_configuration(agent_id: str = Path(...), config_update_payload: AgentConfig = Body(...), handler: AgentConfigHandler = Depends(get_agent_config_handler_dependency)): 
    if agent_id != config_update_payload.agent_id: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path ID vs body ID mismatch.")
    try:
        existing_config = await handler.get_global_agent_config(agent_id)
        if not existing_config: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Global agent ID '{agent_id}' not found.")
        config_update_payload.created_at = existing_config.created_at 
        await handler.save_global_agent_config(config_update_payload)
        updated_config = await handler.get_global_agent_config(agent_id)
        if not updated_config: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve after update.")
        return updated_config
    except IOError as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {e}")
    except ValueError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/configs/global/{agent_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Global Agent Configuration", tags=[TAG_AGENT_CONFIG_GLOBAL], dependencies=[Depends(_check_module_enabled)])
async def delete_global_agent_configuration(agent_id: str = Path(...), handler: AgentConfigHandler = Depends(get_agent_config_handler_dependency)): 
    try:
        if not await handler.delete_global_agent_config(agent_id):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Deletion failed unexpectedly.")
    except ValueError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return 

SESSION_PREFIX = "/sessions/{session_id}/agents"
@router.post(f"{SESSION_PREFIX}/configs", response_model=AgentConfig, status_code=status.HTTP_201_CREATED, summary="Create Session-Scoped Agent Configuration", tags=[TAG_AGENT_CONFIG_LOCAL], dependencies=[Depends(_check_module_enabled)])
async def create_local_agent_configuration(session_id: str = Path(...), config_payload: AgentConfig = Body(...), handler: AgentConfigHandler = Depends(get_agent_config_handler_dependency)): 
    try:
        if await handler.get_local_agent_config(session_id, config_payload.agent_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Local agent ID '{config_payload.agent_id}' already exists in session '{session_id}'.")
        await handler.save_local_agent_config(session_id, config_payload)
        persisted_config = await handler.get_local_agent_config(session_id, config_payload.agent_id)
        if not persisted_config: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve after saving.")
        return persisted_config
    except FileNotFoundError as e: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IOError as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {e}")
    except ValueError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get(f"{SESSION_PREFIX}/configs/{{agent_id}}", response_model=AgentConfig, summary="Get Session-Scoped Agent Configuration", tags=[TAG_AGENT_CONFIG_LOCAL], dependencies=[Depends(_check_module_enabled)])
async def get_local_agent_configuration(session_id: str = Path(...), agent_id: str = Path(...), handler: AgentConfigHandler = Depends(get_agent_config_handler_dependency)): 
    try: config = await handler.get_local_agent_config(session_id, agent_id)
    except FileNotFoundError as e: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not config: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Local agent ID '{agent_id}' not found in session '{session_id}'.")
    return config

@router.get(f"{SESSION_PREFIX}/configs", response_model=List[AgentConfig], summary="List All Session-Scoped Agent Configurations", tags=[TAG_AGENT_CONFIG_LOCAL], dependencies=[Depends(_check_module_enabled)])
async def list_local_agent_configurations(session_id: str = Path(...), handler: AgentConfigHandler = Depends(get_agent_config_handler_dependency)): 
    try: return await handler.list_local_agent_configs(session_id)
    except FileNotFoundError as e: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put(f"{SESSION_PREFIX}/configs/{{agent_id}}", response_model=AgentConfig, summary="Update Session-Scoped Agent Configuration", tags=[TAG_AGENT_CONFIG_LOCAL], dependencies=[Depends(_check_module_enabled)])
async def update_local_agent_configuration(session_id: str = Path(...), agent_id: str = Path(...), config_update_payload: AgentConfig = Body(...), handler: AgentConfigHandler = Depends(get_agent_config_handler_dependency)):  
    if agent_id != config_update_payload.agent_id: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path ID vs body ID mismatch.")
    try:
        existing_config = await handler.get_local_agent_config(session_id, agent_id)
        if not existing_config: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Local agent ID '{agent_id}' not found in session '{session_id}'.")
        config_update_payload.created_at = existing_config.created_at
        await handler.save_local_agent_config(session_id, config_update_payload)
        updated_config = await handler.get_local_agent_config(session_id, agent_id)
        if not updated_config: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve after update.")
        return updated_config
    except FileNotFoundError as e: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IOError as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {e}")
    except ValueError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete(f"{SESSION_PREFIX}/configs/{{agent_id}}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Session-Scoped Agent Configuration", tags=[TAG_AGENT_CONFIG_LOCAL], dependencies=[Depends(_check_module_enabled)])
async def delete_local_agent_configuration(session_id: str = Path(...), agent_id: str = Path(...), handler: AgentConfigHandler = Depends(get_agent_config_handler_dependency)): 
    try:
        if not await handler.delete_local_agent_config(session_id, agent_id):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Deletion failed unexpectedly.")
    except FileNotFoundError as e: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return 

# Agent Execution
@router.post("/run", response_model=AgentRunStatus, summary="Run Agent Task", tags=[TAG_AGENT_EXECUTION], dependencies=[Depends(_check_module_enabled)])
async def run_agent_task_endpoint(
    request: RunAgentRequest = Body(...),
    current_agent_executor: AgentExecutorClass = Depends(get_agent_executor_dependency) 
):
    try:
        run_status_result = await current_agent_executor.run_agent_task(request) 
        if run_status_result.status == "failed":
            error_detail = run_status_result.error_message or "Agent task failed."
            if "not found" in error_detail.lower() and "configuration" in error_detail.lower(): raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_detail)
            elif "service unavailable" in error_detail.lower() or "not loaded" in error_detail.lower() or "Dependency Injection Error" in error_detail: 
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=error_detail)
            else: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_detail)
        return run_status_result
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(e)}")

@router.post("/run/stream", summary="Run Agent Task (Streaming SSE)", tags=[TAG_AGENT_EXECUTION], dependencies=[Depends(_check_module_enabled)])
async def stream_agent_task_outputs_endpoint(
    request: RunAgentRequest = Body(...),
    handler: AgentConfigHandler = Depends(get_agent_config_handler_dependency), 
    current_agent_executor: AgentExecutorClass = Depends(get_agent_executor_dependency),
    current_settings: Settings = Depends(get_settings_dependency), 
    current_llm_manager: Optional[LLMManager] = Depends(get_llm_manager_dependency) 
):
    # DEBUG PRINTS REMOVED
    # print(f"DEBUG_AGENT_ROUTER_STREAM: Endpoint called for agent_id: {request.agent_id}, session_id: {request.session_id}", file=sys.stderr)
    # print(f"DEBUG_AGENT_ROUTER_STREAM: Injected AgentConfigHandler ID: {id(handler)}, type: {type(handler)}", file=sys.stderr)
    # if hasattr(handler, 'settings'):
    #     print(f"DEBUG_AGENT_ROUTER_STREAM: Injected AgentConfigHandler settings ID: {id(handler.settings)}, WORK_SESSIONS_DIR: {handler.settings.WORK_SESSIONS_DIR}", file=sys.stderr)
    # else:
    #     print(f"DEBUG_AGENT_ROUTER_STREAM: Injected AgentConfigHandler does not have 'settings' attribute", file=sys.stderr)
    
    agent_config_instance = await handler.get_effective_agent_config(request.agent_id, request.session_id)
    
    # print(f"DEBUG_AGENT_ROUTER_STREAM: Result of get_effective_agent_config for '{request.agent_id}': {agent_config_instance.name if agent_config_instance else 'Not Found'}", file=sys.stderr)

    if not agent_config_instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent config for '{request.agent_id}' not found.")
    
    if current_settings.ENABLE_LLM_MODULE:
        if not agent_config_instance.llm_model_id: 
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Agent '{agent_config_instance.agent_id}' has no LLM configured.")
        if not current_llm_manager:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="LLM module is enabled but LLMManager failed to initialize.")
        
        # print(f"DEBUG_AGENT_ROUTER_STREAM: Checking LLM '{agent_config_instance.llm_model_id}' with LLM Manager ID: {id(current_llm_manager)}", file=sys.stderr)
        model_info = await current_llm_manager.get_model_details(agent_config_instance.llm_model_id)
        # print(f"DEBUG_AGENT_ROUTER_STREAM: LLM model info: {model_info}", file=sys.stderr)

        if not model_info or not model_info.loaded: 
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"LLM model '{agent_config_instance.llm_model_id}' for agent not loaded.")
    elif agent_config_instance.llm_model_id: 
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Agent needs LLM, but LLM module disabled.")

    async def event_generator():
        try:
            async for chunk in current_agent_executor.stream_agent_task_outputs(request): 
                yield {"event": chunk["type"], "data": json.dumps(chunk)}
        except Exception as e_stream:
            logger.error(f"Error during agent SSE event generation: {e_stream}", exc_info=True)
            error_payload = {"message": str(e_stream), "type": "agent_stream_error"}
            yield {"event": "error", "data": json.dumps(error_payload)}
            
    return EventSourceResponse(event_generator(), media_type="text/event-stream")
