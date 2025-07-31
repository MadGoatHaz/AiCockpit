# acp_backend/routers/llm_service.py
"""
LLM Service Router - Refactored for External AI Services
=====================================================

This module has been refactored to work with external AI services rather than
local LLM hosting. It now serves as an adapter between the application and
the ExternalAIServiceManager.

Author: AiCockpit Development Team
License: GPL-3.0
"""

import json
import logging
from typing import Annotated, AsyncGenerator, Dict, List, Optional, cast

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from sse_starlette.sse import EventSourceResponse

from acp_backend.config import AppSettings
from acp_backend.core.llm_manager import LLMManager
from acp_backend.core.external_ai_manager import AIServiceConfig
from acp_backend.dependencies import get_app_settings, get_llm_manager
from acp_backend.models.llm_models import (
    ChatCompletionRequest,
    DiscoveredLLMConfigResponse,
    LLMChatCompletion,
    LLMConfig,
    LLMModelInfo,
    LLMStatus,
    LoadLLMRequest,
    LoadedLLMsResponse,
    UnloadLLMRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter()
MODULE_NAME = "LLM Service"
TAG_LLM_MODEL_MGMT = "LLM Service Management"
TAG_LLM_CHAT = "LLM Chat Completions"
TAG_EXTERNAL_SERVICES = "External AI Services"

# Type Aliases for Dependencies
SettingsDep = Annotated[AppSettings, Depends(get_app_settings)]
OptionalLLMManagerDep = Annotated[Optional[LLMManager], Depends(get_llm_manager)]


def _check_module_enabled(current_settings: SettingsDep):
    if not current_settings.ENABLE_LLM_SERVICE_MODULE:
        logger.warning(f"{MODULE_NAME} is disabled in configuration.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{MODULE_NAME} is currently disabled.",
        )


def get_llm_manager_checked(
    llm_manager_instance: OptionalLLMManagerDep,
) -> LLMManager:
    if llm_manager_instance is None:
        logger.error(
            "LLMManager is None after module enabled check. This indicates an initialization issue."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LLM Service is enabled but manager failed to initialize.",
        )
    return llm_manager_instance


LLMManagerCheckedDep = Annotated[LLMManager, Depends(get_llm_manager_checked)]


# External AI Service Management Endpoints

@router.post(
    "/services",
    summary="Add External AI Service",
    tags=[TAG_EXTERNAL_SERVICES],
    dependencies=[Depends(_check_module_enabled)],
)
async def add_external_service_endpoint(
    config: AIServiceConfig,
    llm_manager: LLMManagerCheckedDep,
):
    """Add a new external AI service configuration."""
    try:
        success = await llm_manager.add_external_service(config)
        if success:
            return {"message": f"Successfully added external AI service: {config.name}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to add external AI service: {config.name}"
            )
    except Exception as e:
        logger.error(f"Failed to add external AI service: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add external AI service: {str(e)}"
        )


@router.delete(
    "/services/{service_name}",
    summary="Remove External AI Service",
    tags=[TAG_EXTERNAL_SERVICES],
    dependencies=[Depends(_check_module_enabled)],
)
async def remove_external_service_endpoint(
    service_name: str,
    llm_manager: LLMManagerCheckedDep,
):
    """Remove an external AI service configuration."""
    try:
        success = await llm_manager.remove_external_service(service_name)
        if success:
            return {"message": f"Successfully removed external AI service: {service_name}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"External AI service not found: {service_name}"
            )
    except Exception as e:
        logger.error(f"Failed to remove external AI service: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove external AI service: {str(e)}"
        )


@router.post(
    "/services/{service_name}/activate",
    summary="Set Active External AI Service",
    tags=[TAG_EXTERNAL_SERVICES],
    dependencies=[Depends(_check_module_enabled)],
)
async def set_active_service_endpoint(
    service_name: str,
    llm_manager: LLMManagerCheckedDep,
):
    """Set the active external AI service."""
    try:
        success = await llm_manager.set_active_service(service_name)
        if success:
            return {"message": f"Successfully set active AI service: {service_name}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"External AI service not found: {service_name}"
            )
    except Exception as e:
        logger.error(f"Failed to set active AI service: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set active AI service: {str(e)}"
        )


@router.get(
    "/services/test/{service_name}",
    summary="Test Connection to External AI Service",
    tags=[TAG_EXTERNAL_SERVICES],
    dependencies=[Depends(_check_module_enabled)],
)
async def test_service_connection_endpoint(
    service_name: str,
    llm_manager: LLMManagerCheckedDep,
):
    """Test connection to an external AI service."""
    try:
        result = await llm_manager.test_service_connection(service_name)
        if result["success"]:
            return {"message": f"Connection test successful for {service_name}", "result": result}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connection test failed for {service_name}: {result.get('error', 'Unknown error')}"
            )
    except Exception as e:
        logger.error(f"Failed to test connection to external AI service: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test connection: {str(e)}"
        )


@router.get(
    "/services",
    summary="List External AI Services",
    tags=[TAG_EXTERNAL_SERVICES],
    dependencies=[Depends(_check_module_enabled)],
)
async def list_external_services_endpoint(
    llm_manager: LLMManagerCheckedDep,
):
    """List all configured external AI services."""
    try:
        services = await llm_manager.list_external_services()
        return {"services": services}
    except Exception as e:
        logger.error(f"Failed to list external AI services: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list external AI services: {str(e)}"
        )


# Backward Compatibility Endpoints (Refactored for External Services)

@router.get(
    "/models",
    response_model=DiscoveredLLMConfigResponse,
    summary="List Discoverable LLM Models (External Services)",
    tags=[TAG_LLM_MODEL_MGMT],
    dependencies=[Depends(_check_module_enabled)],
)
async def list_available_models_endpoint(llm_manager: LLMManagerCheckedDep):
    """List available models from external AI services."""
    try:
        configs = llm_manager.discover_models()
        return DiscoveredLLMConfigResponse(configs=configs)
    except IOError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to access models: {e}",
        )
    except Exception as e:
        logger.error(f"Failed to list available models: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}",
        )


@router.get(
    "/models/loaded",
    response_model=LoadedLLMsResponse,
    summary="List Currently Loaded LLM Models (External Services)",
    tags=[TAG_LLM_MODEL_MGMT],
    dependencies=[Depends(_check_module_enabled)],
)
async def get_loaded_models_endpoint(llm_manager: LLMManagerCheckedDep):
    """Get metadata for models managed by external services."""
    try:
        loaded_llm_meta_list = llm_manager.get_loaded_models_meta()
        response_models = [
            LLMModelInfo(
                model_id=llm.config.model_id,
                model_name=llm.config.model_name,
                backend_type=llm.config.backend_type,
                status=llm.status,
                parameters=llm.config.parameters,
            )
            for llm in loaded_llm_meta_list
        ]
        return LoadedLLMsResponse(loaded_models=response_models)
    except Exception as e:
        logger.error(f"Failed to get loaded models: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get loaded models: {str(e)}",
        )


@router.post(
    "/models/load",
    response_model=LLMModelInfo,
    status_code=status.HTTP_200_OK,
    summary="Load an LLM Model (External Services)",
    tags=[TAG_LLM_MODEL_MGMT],
    dependencies=[Depends(_check_module_enabled)],
)
async def load_llm_model_endpoint(
    request: Annotated[LoadLLMRequest, Body(...)], llm_manager: LLMManagerCheckedDep
):
    """Load a model through external AI services (backward compatibility)."""
    try:
        model_to_load_config: Optional[LLMConfig] = None
        if request.model_id:
            discovered_configs = llm_manager.discover_models()
            found_config = next(
                (cfg for cfg in discovered_configs if cfg.model_id == request.model_id),
                None,
            )
            if not found_config:
                raise FileNotFoundError(
                    f"Model ID '{request.model_id}' not found in available models."
                )
            model_to_load_config = found_config
        elif hasattr(request, "model_config") and request.model_config:
            model_to_load_config = request.model_config
        else:
            if not request.model_id and not (
                hasattr(request, "model_config") and request.model_config
            ):
                raise ValueError(
                    "Either model_id or model_config must be provided in the request."
                )

        if not model_to_load_config:
            raise ValueError("No valid model configuration to load.")

        loaded_llm_meta = await llm_manager.load_model(model_to_load_config)

        return LLMModelInfo(
            model_id=loaded_llm_meta.config.model_id,
            model_name=loaded_llm_meta.config.model_name,
            backend_type=loaded_llm_meta.config.backend_type,
            status=loaded_llm_meta.status,
            parameters=loaded_llm_meta.config.parameters,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        model_identifier = "N/A"
        if request.model_id:
            model_identifier = request.model_id
        elif hasattr(request, "model_config") and request.model_config:
            model_identifier = request.model_config.model_id
        logger.error(
            f"Error loading model '{model_identifier}': {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load model: {str(e)}",
        )


@router.post(
    "/models/unload",
    response_model=LLMModelInfo,
    summary="Unload an LLM Model (External Services)",
    tags=[TAG_LLM_MODEL_MGMT],
    dependencies=[Depends(_check_module_enabled)],
)
async def unload_llm_model_endpoint(
    request: Annotated[UnloadLLMRequest, Body(...)],
    llm_manager: LLMManagerCheckedDep,
):
    """Unload a model managed by external services (backward compatibility)."""
    model_id = request.model_id
    unloaded_model_meta = llm_manager.get_llm_meta(model_id)

    if not unloaded_model_meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model ID '{model_id}' not found or not loaded, cannot unload.",
        )

    try:
        success = await llm_manager.unload_model(model_id)
        if success:
            return LLMModelInfo(
                model_id=unloaded_model_meta.config.model_id,
                model_name=unloaded_model_meta.config.model_name,
                backend_type=unloaded_model_meta.config.backend_type,
                status=LLMStatus.UNLOADED,
                parameters=unloaded_model_meta.config.parameters,
            )
        else:
            current_meta_after_fail = llm_manager.get_llm_meta(model_id)
            current_status_val = (
                current_meta_after_fail.status.value
                if current_meta_after_fail
                else "Not Found"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to unload model '{model_id}'. Current status: {current_status_val}",
            )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to unload model '{model_id}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unload model: {str(e)}",
        )


@router.get(
    "/models/{model_id}",
    response_model=LLMModelInfo,
    summary="Get Details of a Specific LLM Model (External Services)",
    tags=[TAG_LLM_MODEL_MGMT],
    dependencies=[Depends(_check_module_enabled)],
)
async def get_model_details_endpoint(
    model_id: Annotated[str, Path(..., description="ID of the model.")],
    llm_manager: LLMManagerCheckedDep,
):
    """Get details of a specific model from external services."""
    loaded_llm_meta = llm_manager.get_llm_meta(model_id)
    if loaded_llm_meta:
        return LLMModelInfo(
            model_id=loaded_llm_meta.config.model_id,
            model_name=loaded_llm_meta.config.model_name,
            backend_type=loaded_llm_meta.config.backend_type,
            status=loaded_llm_meta.status,
            parameters=loaded_llm_meta.config.parameters,
        )

    discovered_configs = llm_manager.discover_models()
    found_config = next(
        (cfg for cfg in discovered_configs if cfg.model_id == model_id), None
    )
    if found_config:
        return LLMModelInfo(
            model_id=found_config.model_id,
            model_name=found_config.model_name,
            backend_type=found_config.backend_type,
            status=LLMStatus.DISCOVERED,
            parameters=found_config.parameters,
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=f"Model ID '{model_id}' not found."
    )


@router.post(
    "/chat/completions",
    response_model=LLMChatCompletion,  # For non-streaming
    summary="Create Chat Completion (External Services)",
    tags=[TAG_LLM_CHAT],
    dependencies=[Depends(_check_module_enabled)],
)
async def create_chat_completion_endpoint(
    request: Annotated[ChatCompletionRequest, Body(...)],
    llm_manager: LLMManagerCheckedDep,
):
    """Create a chat completion using external AI services."""
    # In the refactored version, we don't check if the model is "loaded"
    # since models are managed by external services
    
    optional_params = {
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }
    completion_kwargs = {k: v for k, v in optional_params.items() if v is not None}

    if request.stream:
        async def event_generator() -> AsyncGenerator[Dict[str, str], None]:
            try:
                # For streaming, we need to handle the async generator from the external service
                response = await llm_manager.chat_completion(
                    model_id=request.model_id,
                    messages=request.messages,
                    stream=True,
                    **completion_kwargs,
                )
                
                # Handle the streaming response from external service
                async for chunk in response:
                    yield {"event": "message", "data": chunk.model_dump_json()}
                yield {"event": "eos", "data": json.dumps({"message": "End of stream"})}
            except Exception as e_stream:
                logger.error(
                    f"Error during SSE event generation for chat completion: {e_stream}",
                    exc_info=True,
                )
                error_payload = {"error": {"message": str(e_stream), "type": "stream_error"}}
                yield {"event": "error", "data": json.dumps(error_payload)}

        return EventSourceResponse(event_generator(), media_type="text/event-stream")
    else:
        try:
            completion_response = await llm_manager.chat_completion(
                model_id=request.model_id,
                messages=request.messages,
                stream=False,
                **completion_kwargs,
            )
            return cast(LLMChatCompletion, completion_response)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except RuntimeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )
        except Exception as e:
            logger.error(
                f"Unexpected error during non-streaming chat completion: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error: {str(e)}",
            )
