# acp_backend/core/llm_manager.py
import logging
from typing import List, Optional, AsyncGenerator, TypeVar
from pathlib import Path
import asyncio

# Import the class for type hinting, but conditionally use the passed instance
from acp_backend.config import Settings as SettingsClass
from acp_backend.config import settings as global_settings_instance # Fallback

from acp_backend.models.llm_models import (
    LLMModelInfo, LoadModelRequest, ChatCompletionRequest,
    ChatCompletionResponse, ChatCompletionChunk, ChatMessageInput,
    ChatCompletionResponseChoice, ChatCompletionChunkChoice, ChatCompletionChunkDelta,
    UsageInfo
)
from acp_backend.llm_backends.base import LLMBackend
# Import specific backends as needed
from acp_backend.llm_backends.llama_cpp import LlamaCppBackend
# from acp_backend.llm_backends.pie import PIEBackend # If PIEBackend is implemented

logger = logging.getLogger(__name__)

TSettings = TypeVar('TSettings', bound=SettingsClass)

class LLMManager:
    _loaded_models: dict[str, LLMBackend] = {} 

    def __init__(self, settings_override: Optional[TSettings] = None):
        current_settings = settings_override if settings_override else global_settings_instance
        self.settings = current_settings # Store the settings instance used
        
        self.default_backend_type = self.settings.LLM_BACKEND_TYPE 
        logger.info(f"LLMManager initialized with default backend: {self.default_backend_type} using settings ID: {id(self.settings)}")

    async def discover_models(self, models_dir: Optional[Path] = None) -> List[LLMModelInfo]:
        # Use internal settings for models_dir if not provided
        effective_models_dir = models_dir if models_dir is not None else self.settings.MODELS_DIR
        logger.debug(f"Discovering models in {effective_models_dir}")
        
        found_models_info: List[LLMModelInfo] = []
        
        # Add already loaded models
        for model_id, backend_instance in self._loaded_models.items():
            info = backend_instance.get_model_info()
            if info:
                found_models_info.append(info)

        # Scan LlamaCpp models (.gguf files)
        if await asyncio.to_thread(effective_models_dir.exists):
            for file_path in await asyncio.to_thread(list, effective_models_dir.glob("*.gguf")):
                model_id = file_path.stem
                if model_id not in self._loaded_models: # Only add if not already loaded
                    try:
                        size_bytes = await asyncio.to_thread(file_path.stat).st_size
                        size_gb = round(size_bytes / (1024**3), 2) if size_bytes else None
                        # Basic info for discoverable, unloaded GGUF model
                        found_models_info.append(LLMModelInfo(
                            id=model_id,
                            name=model_id, # Or derive a more friendly name
                            path=str(file_path.resolve()),
                            size_gb=size_gb,
                            loaded=False,
                            backend="llama_cpp" # Assuming GGUF is for llama_cpp
                            # Other fields like quantization might need deeper inspection or naming conventions
                        ))
                    except Exception as e:
                        logger.warning(f"Could not get info for GGUF file {file_path}: {e}")
        
        # Placeholder for PIEBackend discovery if it were implemented
        # if self.default_backend_type == "pie" or "pie" in other_enabled_backends:
        #     # pie_models = await PIEBackend.discover_models() # Static method on PIEBackend
        #     # found_models_info.extend(pie_models)
        #     pass

        # Remove duplicates by id, prioritizing loaded models if any conflict
        final_models_dict: Dict[str, LLMModelInfo] = {}
        for model_info in found_models_info:
            if model_info.id not in final_models_dict or model_info.loaded:
                final_models_dict[model_info.id] = model_info
        
        return list(final_models_dict.values())


    async def get_loaded_models(self) -> List[LLMModelInfo]:
        return [model.get_model_info() for model in self._loaded_models.values() if model.get_model_info()]

    async def get_model_details(self, model_id: str) -> Optional[LLMModelInfo]:
        if model_id in self._loaded_models:
            return self._loaded_models[model_id].get_model_info()
        
        # If not loaded, try to find it in discoverable models (e.g., from file system scan)
        # This requires discover_models to be comprehensive or called implicitly.
        # For simplicity, we can call discover_models here if not found in loaded.
        discoverable_models = await self.discover_models() # Uses self.settings.MODELS_DIR
        for model_info in discoverable_models:
            if model_info.id == model_id:
                return model_info # This will have loaded=False if not in _loaded_models
        return None

    async def load_model(self, request: LoadModelRequest) -> LLMModelInfo:
        model_id_to_load = request.model_id or (Path(request.model_path).stem if request.model_path else None)
        if not model_id_to_load:
            raise ValueError("Either model_id or model_path must be provided to load a model.")

        if model_id_to_load in self._loaded_models:
            # Consider just returning the info if already loaded, or raise specific error
            logger.warning(f"Model '{model_id_to_load}' is already loaded. Returning existing info.")
            existing_info = self._loaded_models[model_id_to_load].get_model_info()
            if not existing_info: # Should not happen if it's in _loaded_models
                 raise RuntimeError(f"Model '{model_id_to_load}' in loaded_models dict but get_model_info() failed.")
            return existing_info


        logger.info(f"Attempting to load model: {model_id_to_load} with backend {self.default_backend_type}")

        backend_instance: Optional[LLMBackend] = None

        if self.default_backend_type == "llama_cpp":
            model_path_str = request.model_path
            if not model_path_str:
                # Fallback to settings only if request.model_id was also not enough to find a path
                # This logic might need refinement: discover first, then load by path.
                # For now, if model_path is not given, we assume request.model_id might be a discoverable ID
                # that implies a path, or we use the global default path.
                
                # Attempt to find path from discovered models if only model_id was given
                if request.model_id and not request.model_path:
                    discovered = await self.get_model_details(request.model_id) # Check if it's discoverable
                    if discovered and discovered.path:
                        model_path_str = discovered.path
                    elif self.settings.LLAMA_CPP_MODEL_PATH: # Fallback to global default
                         model_path_str = self.settings.LLAMA_CPP_MODEL_PATH
                    else:
                        raise ValueError(f"Model path not found for '{model_id_to_load}'. Provide 'model_path' or ensure model is discoverable or set LLAMA_CPP_MODEL_PATH.")
                elif self.settings.LLAMA_CPP_MODEL_PATH: # Fallback to global default if no model_id or path
                    model_path_str = self.settings.LLAMA_CPP_MODEL_PATH
                else:
                     raise ValueError("llama-cpp backend requires 'model_path' in request or LLAMA_CPP_MODEL_PATH in settings.")


            model_path_obj = Path(model_path_str)
            if not await asyncio.to_thread(model_path_obj.exists):
                raise FileNotFoundError(f"Model file not found at {model_path_obj}")

            try:
                backend_instance = LlamaCppBackend(
                    model_path=model_path_obj,
                    n_gpu_layers=request.n_gpu_layers if request.n_gpu_layers is not None else self.settings.LLAMA_CPP_N_GPU_LAYERS,
                    n_ctx=request.n_ctx if request.n_ctx is not None else self.settings.LLAMA_CPP_N_CTX,
                    n_batch=request.n_batch if request.n_batch is not None else self.settings.LLAMA_CPP_N_BATCH,
                    chat_format=request.chat_format or self.settings.LLAMA_CPP_CHAT_FORMAT,
                    verbose=self.settings.LLAMA_CPP_VERBOSE
                )
            except Exception as e: # Catch specific errors from LlamaCppBackend if possible
                logger.error(f"Failed to initialize LlamaCppBackend for model '{model_id_to_load}': {e}", exc_info=True)
                raise RuntimeError(f"Failed to initialize LlamaCppBackend for model '{model_id_to_load}': {e}")
        
        # Placeholder for PIEBackend
        # elif self.default_backend_type == "pie":
        #     if not request.model_id: # PIE might use IDs more than paths
        #         raise ValueError("PIE backend requires 'model_id'.")
        #     backend_instance = PIEBackend(model_id=request.model_id, settings=self.settings) # Pass settings if needed

        else:
            raise ValueError(f"Unsupported LLM backend type: {self.default_backend_type}")

        if backend_instance:
            self._loaded_models[model_id_to_load] = backend_instance
            model_info = backend_instance.get_model_info()
            if not model_info: # Should not happen
                logger.error(f"Backend for '{model_id_to_load}' failed to provide model info after load.")
                # Clean up if info is missing
                self._loaded_models.pop(model_id_to_load, None)
                backend_instance.release()
                raise RuntimeError(f"Backend for '{model_id_to_load}' failed to provide model info after load.")
            
            logger.info(f"Model '{model_id_to_load}' loaded successfully with backend {type(backend_instance).__name__}.")
            return model_info
        else: # Should have been caught by backend type check, but as a safeguard
            raise RuntimeError(f"Could not create backend instance for model '{model_id_to_load}'.")


    async def unload_model(self, model_id: str) -> LLMModelInfo:
        if model_id not in self._loaded_models:
            # Check if it's a discoverable but not loaded model to return its info
            details = await self.get_model_details(model_id)
            if details: # It exists but is not loaded
                logger.info(f"Model '{model_id}' was not loaded. Returning its current info.")
                return details
            raise ValueError(f"Model '{model_id}' not found or not loaded.")
        
        backend = self._loaded_models.pop(model_id)
        original_info = backend.get_model_info() # Get info before releasing
        
        try:
            await asyncio.to_thread(backend.release) # Assuming release can be blocking
        except Exception as e:
            logger.error(f"Error during release of model '{model_id}': {e}", exc_info=True)
            # Even if release fails, it's removed from loaded_models. What to return?
            # Fallback to original_info but mark as not loaded.
            if original_info:
                original_info.loaded = False
                return original_info
            # If original_info was None, construct a basic one
            return LLMModelInfo(id=model_id, name=model_id, backend=self.default_backend_type, loaded=False, path=str(getattr(backend, '_model_path', 'N/A')))


        logger.info(f"Model '{model_id}' unloaded successfully.")
        if original_info:
            original_info.loaded = False
            return original_info
        # Fallback if get_model_info somehow failed before release but model was popped
        return LLMModelInfo(id=model_id, name=model_id, backend=self.default_backend_type, loaded=False, path=str(getattr(backend, '_model_path', 'N/A')))


    async def process_chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        backend = self._loaded_models.get(request.model_id)
        if not backend:
            raise ValueError(f"Model '{request.model_id}' is not loaded.")
        
        return await backend.chat_completion(request)

    async def stream_process_chat_completion(self, request: ChatCompletionRequest) -> AsyncGenerator[ChatCompletionChunk, None]:
        backend = self._loaded_models.get(request.model_id)
        if not backend:
            raise ValueError(f"Model '{request.model_id}' is not loaded.")
        
        async for chunk in backend.stream_chat_completion(request):
            yield chunk
