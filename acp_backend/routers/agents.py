# acp_backend/routers/agents.py
import json
import logging
from typing import Annotated, AsyncGenerator, Dict, List, Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query, # Ensure Query is imported
    status,
)
from sse_starlette.sse import EventSourceResponse

from acp_backend.config import AppSettings
from acp_backend.core.agent_config_handler import AgentConfigHandler
from acp_backend.core.agent_executor import AgentExecutor as AgentExecutorClass
# LLMManager not directly used in this router's endpoints, only for AgentExecutorCheckedDep type hint
from acp_backend.core.llm_manager import LLMManager
from acp_backend.dependencies import (
    get_agent_config_handler,
    get_agent_executor,
    get_app_settings,
    get_llm_manager, # Imported for OptionalLLMManagerDep if needed by AgentExecutorCheckedDep
)
from acp_backend.models.agent_models import (
    AgentConfig,
    AgentOutputChunk,
    AgentRunStatus,
    RunAgentRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter()
MODULE_NAME = "Agents Service"
TAG_AGENT_CONFIG_GLOBAL = "Agent Configuration (Global)"
TAG_AGENT_CONFIG_LOCAL = "Agent Configuration (Session-Scoped)"
TAG_AGENT_EXECUTION = "Agent Execution"

# Type Aliases for Dependencies
SettingsDep = Annotated[AppSettings, Depends(get_app_settings)]
AgentConfigHandlerDep = Annotated[AgentConfigHandler, Depends(get_agent_config_handler)]


def _get_agent_executor_checked_dependency(
    agent_executor_instance: Annotated[
        Optional[AgentExecutorClass], Depends(get_agent_executor)
    ],
) -> AgentExecutorClass:
    if agent_executor_instance is None:
        logger.error(
            "AgentExecutor is None after module enabled check. This indicates an initialization issue."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agents Service is enabled but executor failed to initialize.",
        )
    return agent_executor_instance


AgentExecutorCheckedDep = Annotated[
    AgentExecutorClass, Depends(_get_agent_executor_checked_dependency)
]


def _check_module_enabled(current_settings: SettingsDep):
    if not current_settings.ENABLE_AGENTS_MODULE:
        logger.warning(f"{MODULE_NAME} is disabled in configuration.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{MODULE_NAME} is currently disabled.",
        )


# Global Agent Configurations
@router.post(
    "/configs/global",
    response_model=AgentConfig,
    status_code=status.HTTP_201_CREATED,
    summary="Create Global Agent Configuration",
    tags=[TAG_AGENT_CONFIG_GLOBAL],
    dependencies=[Depends(_check_module_enabled)],
)
async def create_global_agent_configuration(
    config_payload: Annotated[AgentConfig, Body(...)],
    handler: AgentConfigHandlerDep,
):
    try:
        if await handler.get_global_agent_config(config_payload.agent_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Global agent ID '{config_payload.agent_id}' already exists.",
            )
        await handler.save_global_agent_config(config_payload)
        persisted_config = await handler.get_global_agent_config(
            config_payload.agent_id
        )
        if not persisted_config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve after saving.",
            )
        return persisted_config
    except IOError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {e}"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/configs/global/{agent_id}",
    response_model=AgentConfig,
    summary="Get Global Agent Configuration",
    tags=[TAG_AGENT_CONFIG_GLOBAL],
    dependencies=[Depends(_check_module_enabled)],
)
async def get_global_agent_configuration(
    agent_id: Annotated[str, Path(..., title="Agent ID")],
    handler: AgentConfigHandlerDep,
):
    try:
        config = await handler.get_global_agent_config(agent_id)
    except ValueError as e:  # From _validate_agent_id_format
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Global agent ID '{agent_id}' not found.",
        )
    return config


@router.get(
    "/configs/global",
    response_model=List[AgentConfig],
    summary="List All Global Agent Configurations",
    tags=[TAG_AGENT_CONFIG_GLOBAL],
    dependencies=[Depends(_check_module_enabled)],
)
async def list_all_global_agent_configurations(handler: AgentConfigHandlerDep):
    return await handler.list_global_agent_configs()


@router.put(
    "/configs/global/{agent_id}",
    response_model=AgentConfig,
    summary="Update Global Agent Configuration",
    tags=[TAG_AGENT_CONFIG_GLOBAL],
    dependencies=[Depends(_check_module_enabled)],
)
async def update_global_agent_configuration(
    agent_id: Annotated[str, Path(..., title="Agent ID")],
    config_update_payload: Annotated[AgentConfig, Body(...)],
    handler: AgentConfigHandlerDep,
):
    if agent_id != config_update_payload.agent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path agent_id does not match agent_id in request body.",
        )
    try:
        existing_config = await handler.get_global_agent_config(agent_id)
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Global agent ID '{agent_id}' not found.",
            )
        config_update_payload.created_at = existing_config.created_at
        await handler.save_global_agent_config(config_update_payload)
        updated_config = await handler.get_global_agent_config(agent_id)
        if not updated_config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve agent config after update.",
            )
        return updated_config
    except IOError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {e}"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/configs/global/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Global Agent Configuration",
    tags=[TAG_AGENT_CONFIG_GLOBAL],
    dependencies=[Depends(_check_module_enabled)],
)
async def delete_global_agent_configuration(
    agent_id: Annotated[str, Path(..., title="Agent ID")],
    handler: AgentConfigHandlerDep,
):
    try:
        success = await handler.delete_global_agent_config(agent_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Global agent ID '{agent_id}' not found for deletion.",
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IOError as e:
        logger.error(f"IOError deleting global agent config '{agent_id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not delete agent config: {e}",
        )
    return


# Session-Scoped Agent Configurations
SESSION_PREFIX = "/sessions/{session_id}/agents"


@router.post(
    f"{SESSION_PREFIX}/configs",
    response_model=AgentConfig,
    status_code=status.HTTP_201_CREATED,
    summary="Create Session-Scoped Agent Configuration",
    tags=[TAG_AGENT_CONFIG_LOCAL],
    dependencies=[Depends(_check_module_enabled)],
)
async def create_local_agent_configuration(
    session_id: Annotated[str, Path(..., title="Session ID")],
    config_payload: Annotated[AgentConfig, Body(...)],
    handler: AgentConfigHandlerDep,
):
    try:
        if await handler.get_local_agent_config(
            session_id, config_payload.agent_id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Local agent ID '{config_payload.agent_id}' already exists in session '{session_id}'.",
            )
        await handler.save_local_agent_config(session_id, config_payload)
        persisted_config = await handler.get_local_agent_config(
            session_id, config_payload.agent_id
        )
        if not persisted_config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve after saving local agent config.",
            )
        return persisted_config
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IOError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {e}"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    f"{SESSION_PREFIX}/configs/{{agent_id}}",
    response_model=AgentConfig,
    summary="Get Session-Scoped Agent Configuration",
    tags=[TAG_AGENT_CONFIG_LOCAL],
    dependencies=[Depends(_check_module_enabled)],
)
async def get_local_agent_configuration(
    session_id: Annotated[str, Path(..., title="Session ID")],
    agent_id: Annotated[str, Path(..., title="Agent ID")],
    handler: AgentConfigHandlerDep,
):
    try:
        config = await handler.get_local_agent_config(session_id, agent_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local agent ID '{agent_id}' not found in session '{session_id}'.",
        )
    return config


@router.get(
    f"{SESSION_PREFIX}/configs",
    response_model=List[AgentConfig],
    summary="List All Session-Scoped Agent Configurations",
    tags=[TAG_AGENT_CONFIG_LOCAL],
    dependencies=[Depends(_check_module_enabled)],
)
async def list_local_agent_configurations(
    session_id: Annotated[str, Path(..., title="Session ID")],
    handler: AgentConfigHandlerDep,
):
    try:
        return await handler.list_local_agent_configs(session_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    f"{SESSION_PREFIX}/configs/{{agent_id}}",
    response_model=AgentConfig,
    summary="Update Session-Scoped Agent Configuration",
    tags=[TAG_AGENT_CONFIG_LOCAL],
    dependencies=[Depends(_check_module_enabled)],
)
async def update_local_agent_configuration(
    session_id: Annotated[str, Path(..., title="Session ID")],
    agent_id: Annotated[str, Path(..., title="Agent ID")],
    config_update_payload: Annotated[AgentConfig, Body(...)],
    handler: AgentConfigHandlerDep,
):
    if agent_id != config_update_payload.agent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path agent_id does not match agent_id in request body.",
        )
    try:
        existing_config = await handler.get_local_agent_config(session_id, agent_id)
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Local agent ID '{agent_id}' not found in session '{session_id}'.",
            )
        config_update_payload.created_at = existing_config.created_at
        await handler.save_local_agent_config(session_id, config_update_payload)
        updated_config = await handler.get_local_agent_config(session_id, agent_id)
        if not updated_config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve agent config after update.",
            )
        return updated_config
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IOError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {e}"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    f"{SESSION_PREFIX}/configs/{{agent_id}}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Session-Scoped Agent Configuration",
    tags=[TAG_AGENT_CONFIG_LOCAL],
    dependencies=[Depends(_check_module_enabled)],
)
async def delete_local_agent_configuration(
    session_id: Annotated[str, Path(..., title="Session ID")],
    agent_id: Annotated[str, Path(..., title="Agent ID")],
    handler: AgentConfigHandlerDep,
):
    try:
        success = await handler.delete_local_agent_config(session_id, agent_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Local agent ID '{agent_id}' in session '{session_id}' not found for deletion.",
            )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IOError as e:
        logger.error(
            f"IOError deleting local agent config '{agent_id}' for session '{session_id}': {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not delete agent config: {e}",
        )
    return


# Agent Execution
@router.post(
    "/run",
    response_model=AgentRunStatus,
    summary="Run Agent Task",
    tags=[TAG_AGENT_EXECUTION],
    dependencies=[Depends(_check_module_enabled)],
)
async def run_agent_task_endpoint(
    request: Annotated[RunAgentRequest, Body(...)],
    agent_executor: AgentExecutorCheckedDep,
):
    try:
        run_status_result = await agent_executor.run_agent_task(request)
        if run_status_result.status == "failed":
            error_detail = (
                run_status_result.error_message
                or "Agent task failed without specific error."
            )
            if "not found" in error_detail.lower() and (
                "configuration" in error_detail.lower()
                or "agent" in error_detail.lower()
            ):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=error_detail
                )
            elif (
                "service unavailable" in error_detail.lower()
                or "not loaded" in error_detail.lower()
                or "Dependency Injection Error" in error_detail
                or "LLMManager not available" in error_detail
                or "failed to initialize" in error_detail.lower()
            ):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=error_detail,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_detail,
                )
        return run_status_result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in agent run endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during agent run: {str(e)}",
        )


@router.post(
    "/run/stream",
    summary="Run Agent Task (Streaming SSE)",
    tags=[TAG_AGENT_EXECUTION],
    dependencies=[Depends(_check_module_enabled)],
)
async def stream_agent_task_outputs_endpoint(
    request: Annotated[RunAgentRequest, Body(...)],
    agent_executor: AgentExecutorCheckedDep,
):
    async def event_generator() -> AsyncGenerator[Dict[str, str], None]:
        try:
            async for chunk_model in agent_executor.stream_agent_task_outputs(
                request
            ):
                yield {"event": chunk_model.type, "data": chunk_model.model_dump_json()}
        except Exception as e_stream:
            logger.error(
                f"Error during agent SSE event generation: {e_stream}", exc_info=True
            )
            error_payload = {
                "message": str(e_stream),
                "type": "agent_stream_error",
            }
            yield {"event": "error", "data": json.dumps(error_payload)}

    return EventSourceResponse(event_generator(), media_type="text/event-stream")
