# acp_backend/routers/llm_service.py
import logging
import json 
import sys 
from typing import List, AsyncGenerator, Optional 
from fastapi import APIRouter, HTTPException, Body, Path, status, Depends
from sse_starlette.sse import EventSourceResponse 

from acp_backend.config import settings, Settings 
from acp_backend.core.llm_manager import LLMManager 
from acp_backend.dependencies import get_llm_manager_dependency, get_settings_dependency

from acp_backend.models.llm_models import (
    LLMModelInfo, LoadModelRequest,
    ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChunk
)

logger = logging.getLogger(__name__)
router = APIRouter()
MODULE_NAME = "LLM Service"
TAG_LLM_MODEL_MGMT = "LLM Model Management"
TAG_LLM_CHAT = "LLM Chat Completions"

def _check_module_enabled(current_settings: Settings = Depends(get_settings_dependency)):
    if not current_settings.ENABLE_LLM_MODULE:
        logger.warning(f"{MODULE_NAME} is disabled in configuration.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"{MODULE_NAME} is currently disabled.")

@router.get("/models/available", response_model=List[LLMModelInfo], summary="List Discoverable LLM Models", tags=[TAG_LLM_MODEL_MGMT], dependencies=[Depends(_check_module_enabled)])
async def list_available_models_endpoint(current_llm_manager: LLMManager = Depends(get_llm_manager_dependency)):
    try: return await current_llm_manager.discover_models() # Uses internal settings for path
    except IOError as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to access models directory: {e}")
    except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list models: {e}")

@router.get("/models/loaded", response_model=List[LLMModelInfo], summary="List Currently Loaded LLM Models", tags=[TAG_LLM_MODEL_MGMT], dependencies=[Depends(_check_module_enabled)])
async def get_loaded_models_endpoint(current_llm_manager: LLMManager = Depends(get_llm_manager_dependency)):
    try: return await current_llm_manager.get_loaded_models()
    except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to get loaded models: {e}")

@router.post("/models/load", response_model=LLMModelInfo, status_code=status.HTTP_200_OK, summary="Load an LLM Model", tags=[TAG_LLM_MODEL_MGMT], dependencies=[Depends(_check_module_enabled)])
async def load_llm_model_endpoint(request: LoadModelRequest = Body(...), current_llm_manager: LLMManager = Depends(get_llm_manager_dependency)):
    try: return await current_llm_manager.load_model(request)
    except FileNotFoundError as e: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {e}")

@router.post("/models/unload/{model_id}", response_model=LLMModelInfo, summary="Unload an LLM Model", tags=[TAG_LLM_MODEL_MGMT], dependencies=[Depends(_check_module_enabled)])
async def unload_llm_model_endpoint(model_id: str = Path(..., description="ID of model to unload."), current_llm_manager: LLMManager = Depends(get_llm_manager_dependency)):
    try: return await current_llm_manager.unload_model(model_id)
    except ValueError as e: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) # Could be 400 if model_id is invalid format
    except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to unload model: {e}")

@router.get("/models/{model_id}", response_model=LLMModelInfo, summary="Get Details of a Specific LLM Model", tags=[TAG_LLM_MODEL_MGMT], dependencies=[Depends(_check_module_enabled)])
async def get_model_details_endpoint(model_id: str = Path(..., description="ID of the model."), current_llm_manager: LLMManager = Depends(get_llm_manager_dependency)):
    details = await current_llm_manager.get_model_details(model_id) # This now checks discoverable too
    if not details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Model ID '{model_id}' not found.")
    return details

@router.post("/chat/completions", response_model=None, summary="Create Chat Completion", tags=[TAG_LLM_CHAT], dependencies=[Depends(_check_module_enabled)])
async def create_chat_completion_endpoint(request: ChatCompletionRequest = Body(...), current_llm_manager: LLMManager = Depends(get_llm_manager_dependency)):
    # DEBUG PRINT REMOVED
    
    model_info = await current_llm_manager.get_model_details(request.model_id)
    
    # DEBUG PRINT REMOVED
    
    if not model_info or not model_info.loaded:
        # DEBUG PRINT REMOVED
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Model '{request.model_id}' not loaded.")
    
    if request.stream:
        # DEBUG PRINT REMOVED
        async def event_generator():
            try:
                async for chunk in current_llm_manager.stream_process_chat_completion(request):
                    yield {"data": json.dumps(chunk)}
            except Exception as e:
                logger.error(f"Error during SSE event generation: {e}", exc_info=True)
                error_payload = {"error": {"message": str(e), "type": "stream_error"}}
                yield f"event: error\ndata: {json.dumps(error_payload)}\n\n" 
        return EventSourceResponse(event_generator(), media_type="text/event-stream")
    else: 
        # DEBUG PRINT REMOVED
        try: 
            return await current_llm_manager.process_chat_completion(request)
        except ValueError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except RuntimeError as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {e}")
