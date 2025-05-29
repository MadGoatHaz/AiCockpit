# acp_backend/core/llm_manager.py
import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Type, AsyncGenerator
import asyncio
from collections import defaultdict

from acp_backend.config import AppSettings # Assuming this is correctly imported

from acp_backend.models.llm_models import (
    LLM,
    LLMConfig,
    LLMChatMessage,
    LLMChatCompletion, # Using the canonical name
    LLMModelType,
    LLMStatus,
)
from acp_backend.llm_backends.base import LLMBackendInterface
from acp_backend.llm_backends.llama_cpp import LlamaCppBackend
# from acp_backend.llm_backends.pie import PIEBackend # If you implement this

logger = logging.getLogger(__name__)

# Mapping of backend type strings to backend classes
BACKEND_CLASSES: Dict[LLMModelType, Type[LLMBackendInterface]] = {
    LLMModelType.LLAMA_CPP: LlamaCppBackend,
    # LLMModelType.PIE: PIEBackend,
}

class LLMManager:
    def __init__(
        self,
        models_dir: str | Path,
        default_backend_type: LLMModelType | str,
        # app_settings_instance: AppSettings # Optionally pass full settings if needed by backends
    ):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        if isinstance(default_backend_type, str):
            try:
                self.default_backend_type = LLMModelType(default_backend_type.lower())
            except ValueError:
                logger.error(f"Invalid default_backend_type string: {default_backend_type}. Falling back to {LLMModelType.LLAMA_CPP.value}.")
                self.default_backend_type = LLMModelType.LLAMA_CPP
        else:
            self.default_backend_type = default_backend_type

        # self.app_settings = app_settings_instance # Store if needed

        self.loaded_models: Dict[str, LLM] = {} # Stores LLM Pydantic model (config & status)
        self._live_backends: Dict[str, LLMBackendInterface] = {} # Stores live backend instances
        self._model_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock) # Added for per-model locking

        logger.info(
            f"LLMManager initialized. Models directory: {self.models_dir}. "
            f"Default backend: {self.default_backend_type.value}"
        )

    def _get_backend_class(self, backend_type: Optional[LLMModelType]) -> Type[LLMBackendInterface]:
        effective_backend_type = backend_type or self.default_backend_type
        backend_class = BACKEND_CLASSES.get(effective_backend_type)
        if not backend_class:
            logger.error(
                f"Unsupported LLM backend type: {effective_backend_type}. "
                f"Falling back to {self.default_backend_type.value} if available."
            )
            if effective_backend_type != self.default_backend_type:
                backend_class = BACKEND_CLASSES.get(self.default_backend_type)
            if not backend_class:
                raise ValueError(f"No backend class configured for '{effective_backend_type.value}' or default type.")
        return backend_class

    def discover_models(self, backend_filter: Optional[LLMModelType | str] = None) -> List[LLMConfig]:
        logger.info(f"Discovering models (currently mocked). Backend filter: {backend_filter}")
        mock_configs = [
            LLMConfig(
                model_id="mock-model-llama-cpp",
                model_name="Mock Llama Cpp Model",
                model_path="mock-model.gguf", # Path relative to models_dir for local backends
                backend_type=LLMModelType.LLAMA_CPP,
                parameters={"n_ctx": 2048, "n_gpu_layers": 0}
            ),
        ]
        if backend_filter:
            filter_val = LLMModelType(str(backend_filter).lower()) if isinstance(backend_filter, str) else backend_filter
            return [config for config in mock_configs if config.backend_type == filter_val]
        return mock_configs

    async def load_model(self, model_config: LLMConfig) -> LLM:
        model_id = model_config.model_id
        async with self._model_locks[model_id]: # Acquire lock for this model_id
            if model_id in self.loaded_models and self.loaded_models[model_id].status == LLMStatus.LOADED:
                logger.info(f"Model '{model_id}' already loaded.")
                return self.loaded_models[model_id]

            logger.info(f"Loading model '{model_id}' ({model_config.model_name}) "
                        f"using backend: {model_config.backend_type.value}")
        
            # Store metadata immediately with loading status
            llm_meta = LLM(config=model_config, status=LLMStatus.LOADING)
            self.loaded_models[model_id] = llm_meta

            try:
                BackendClass = self._get_backend_class(model_config.backend_type)
                
                actual_model_path = model_config.model_path
                # For local file-based backends, resolve path relative to models_dir if not absolute
                if model_config.backend_type == LLMModelType.LLAMA_CPP: # Add other local types if any
                    if not Path(actual_model_path).is_absolute():
                        actual_model_path = str(self.models_dir / model_config.model_path)
                
                # Create and load the backend instance
                # Pass AppSettings if specific backend initializers need more global config
                # backend_instance = BackendClass(model_path=actual_model_path, config_params=model_config.parameters, app_settings=self.app_settings)
                backend_instance = BackendClass(model_path=actual_model_path, config_params=model_config.parameters)
                await backend_instance.load() 

                self._live_backends[model_id] = backend_instance # Store live backend
                llm_meta.status = LLMStatus.LOADED
                logger.info(f"Successfully loaded model '{model_id}'.")
                return llm_meta
            except Exception as e:
                logger.error(f"Failed to load model '{model_id}': {e}", exc_info=True)
                llm_meta.status = LLMStatus.ERROR
                llm_meta.error_message = str(e)
                if model_id in self._live_backends: # Cleanup if backend was partially stored
                    del self._live_backends[model_id]
                raise # Re-raise to allow caller to handle

    async def unload_model(self, model_id: str) -> bool:
        async with self._model_locks[model_id]: # Acquire lock for this model_id
            if model_id not in self.loaded_models:
                logger.warning(f"Model '{model_id}' not found in metadata. Cannot unload.")
                return False
        
            llm_meta = self.loaded_models[model_id]
            llm_meta.status = LLMStatus.UNLOADING

            try:
                logger.info(f"Unloading model '{model_id}'...")
                backend_instance = self._live_backends.pop(model_id, None)
                if backend_instance and hasattr(backend_instance, 'unload'):
                    await backend_instance.unload() # Assuming an async unload method
                
                del self.loaded_models[model_id]
                import gc
                gc.collect() # Hint for garbage collection
                logger.info(f"Successfully unloaded model '{model_id}'.")
                return True
            except Exception as e:
                logger.error(f"Error unloading model '{model_id}': {e}", exc_info=True)
                llm_meta.status = LLMStatus.ERROR # Mark as error if unload fails
                llm_meta.error_message = f"Failed to unload: {str(e)}"
                # Do not re-add to _live_backends if pop failed or unload errored
                return False

    def get_loaded_models_meta(self) -> List[LLM]: # Returns list of LLM Pydantic models
        return list(self.loaded_models.values())

    def get_llm_meta(self, model_id: str) -> Optional[LLM]:
        return self.loaded_models.get(model_id)

    def _get_live_backend(self, model_id: str) -> Optional[LLMBackendInterface]:
        llm_meta = self.get_llm_meta(model_id)
        if not llm_meta or llm_meta.status != LLMStatus.LOADED:
            logger.error(f"Cannot get live backend for model '{model_id}'. Status: {llm_meta.status if llm_meta else 'Not Found'}")
            return None
        
        backend_instance = self._live_backends.get(model_id)
        if not backend_instance:
            logger.error(f"Live backend instance for model '{model_id}' not found, though metadata status is LOADED. This indicates an internal inconsistency.")
            # Potentially try to reload or mark as error
            llm_meta.status = LLMStatus.ERROR
            llm_meta.error_message = "Internal error: Live backend instance missing."
            return None
        return backend_instance

    async def chat_completion(
        self, model_id: str, messages: List[LLMChatMessage], stream: bool = False, **kwargs
    ) -> LLMChatCompletion | AsyncGenerator[LLMChatCompletion, None]:
        
        backend_instance = self._get_live_backend(model_id)
        if not backend_instance:
            raise ValueError(f"Model '{model_id}' is not loaded or backend instance is unavailable.")

        llm_meta = self.get_llm_meta(model_id) # Should exist if backend_instance was found
        
        logger.debug(f"Performing chat completion with model '{model_id}'. Stream: {stream}. Kwargs: {kwargs}")
        
        # Pass the model_id from the config to be included in the response object
        return await backend_instance.chat_completion(
            messages, 
            stream=stream, 
            model_id_for_response=llm_meta.config.model_id, 
            **kwargs
        )

    async def unload_all_models(self):
        logger.info("Unloading all loaded models...")
        model_ids_to_unload = list(self.loaded_models.keys()) # Iterate over a copy of keys
        for model_id in model_ids_to_unload:
            await self.unload_model(model_id)
        logger.info("All models have been requested to unload.")
