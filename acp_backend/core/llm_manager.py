# acp_backend/core/llm_manager.py
"""
LLM Manager - Refactored for External AI Services
===============================================

This module has been refactored to work with external AI services rather than
local LLM hosting. It now serves as an adapter between the application and
the ExternalAIServiceManager.

Author: AiCockpit Development Team
License: GPL-3.0
"""

import logging
from typing import Optional, List, Dict, Any, AsyncGenerator
import asyncio
from collections import defaultdict

from acp_backend.config import AppSettings
from acp_backend.core.external_ai_manager import (
    external_ai_manager,
    AIServiceConfig,
    ChatMessage,
    ChatCompletionRequest
)

# Import models for compatibility
from acp_backend.models.llm_models import (
    LLM,
    LLMConfig,
    LLMChatMessage,
    LLMChatCompletion,
    LLMModelType,
    LLMStatus,
)

logger = logging.getLogger(__name__)


class LLMManager:
    """Refactored LLM Manager that works with external AI services."""
    
    def __init__(
        self,
        models_dir: str | None = None,  # Not used in refactored version
        default_backend_type: str = "external",  # Always use external services
        app_settings_instance: AppSettings = None
    ):
        self.app_settings = app_settings_instance
        self.default_backend_type = "external"
        
        # For compatibility with existing code
        self.loaded_models: Dict[str, LLM] = {}
        self._model_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        
        logger.info("LLMManager initialized for external AI services")

    async def initialize_default_service(self):
        """Initialize a default external AI service for backward compatibility."""
        # This would typically be configured through environment variables
        # For now, we'll set up a default configuration that can be overridden
        default_config = AIServiceConfig(
            name="default",
            type="lmstudio",
            base_url="http://localhost:1234/v1",  # Default LM Studio endpoint
            model="gpt-3.5-turbo"  # Default model
        )
        
        success = await external_ai_manager.add_service(default_config)
        if success:
            await external_ai_manager.set_active_service("default")
            logger.info("Initialized default external AI service")
        else:
            logger.warning("Failed to initialize default external AI service")

    def discover_models(self, backend_filter: Optional[str] = None) -> List[LLMConfig]:
        """Discover available models from external services."""
        logger.info("Discovering models from external AI services")
        # In a real implementation, this would query the external services
        # For now, we'll return a mock list
        mock_configs = [
            LLMConfig(
                model_id="gpt-3.5-turbo",
                model_name="GPT-3.5 Turbo",
                model_path="",  # Not used for external services
                backend_type=LLMModelType.LLAMA_CPP,  # For compatibility
                parameters={"temperature": 0.7, "max_tokens": 1000}
            ),
            LLMConfig(
                model_id="gpt-4",
                model_name="GPT-4",
                model_path="",
                backend_type=LLMModelType.LLAMA_CPP,
                parameters={"temperature": 0.7, "max_tokens": 2000}
            ),
        ]
        return mock_configs

    async def add_external_service(self, config: AIServiceConfig) -> bool:
        """Add an external AI service."""
        return await external_ai_manager.add_service(config)

    async def remove_external_service(self, name: str) -> bool:
        """Remove an external AI service."""
        return await external_ai_manager.remove_service(name)

    async def set_active_service(self, name: str) -> bool:
        """Set the active external AI service."""
        return await external_ai_manager.set_active_service(name)

    async def test_service_connection(self, name: str) -> Dict[str, Any]:
        """Test connection to an external AI service."""
        return await external_ai_manager.test_connection(name)

    async def list_external_services(self) -> List[Dict[str, Any]]:
        """List all configured external services."""
        return await external_ai_manager.list_services()

    async def chat_completion(
        self,
        model_id: str,
        messages: List[LLMChatMessage],
        stream: bool = False,
        **kwargs
    ) -> LLMChatCompletion | AsyncGenerator[LLMChatCompletion, None]:
        """
        Perform chat completion using external AI services.
        
        Args:
            model_id: Model identifier (used for compatibility)
            messages: List of chat messages
            stream: Whether to stream the response
            **kwargs: Additional parameters
            
        Returns:
            Chat completion response or async generator for streaming
        """
        try:
            # Convert messages to the format expected by ExternalAIServiceManager
            external_messages = [
                ChatMessage(role=msg.role, content=msg.content)
                for msg in messages
            ]
            
            # Create request
            request = ChatCompletionRequest(
                messages=external_messages,
                model=model_id,  # Pass model_id to external service
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', None),
                stream=stream
            )
            
            # Perform chat completion using external service
            response = await external_ai_manager.chat_completion(request)
            
            # For streaming responses, return directly
            if stream:
                return response
                
            # For non-streaming responses, convert to LLMChatCompletion
            # This maintains compatibility with existing code
            return LLMChatCompletion(
                id=response.id,
                choices=[
                    {
                        "index": choice.get("index", 0),
                        "message": {
                            "role": "assistant",
                            "content": choice.get("message", {}).get("content", "")
                        },
                        "finish_reason": choice.get("finish_reason", "stop")
                    }
                    for choice in response.choices
                ],
                created=response.created,
                model=response.model,
                object="chat.completion",
                usage=response.usage or {}
            )
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise

    # Backward compatibility methods
    async def load_model(self, model_config: LLMConfig) -> LLM:
        """Backward compatibility method - models are not loaded locally."""
        logger.warning("load_model called but models are managed externally")
        llm_meta = LLM(config=model_config, status=LLMStatus.LOADED)
        self.loaded_models[model_config.model_id] = llm_meta
        return llm_meta

    async def unload_model(self, model_id: str) -> bool:
        """Backward compatibility method - models are not unloaded locally."""
        logger.warning("unload_model called but models are managed externally")
        if model_id in self.loaded_models:
            del self.loaded_models[model_id]
        return True

    def get_loaded_models_meta(self) -> List[LLM]:
        """Get metadata for loaded models."""
        return list(self.loaded_models.values())

    def get_llm_meta(self, model_id: str) -> Optional[LLM]:
        """Get metadata for a specific model."""
        return self.loaded_models.get(model_id)

    async def unload_all_models(self):
        """Backward compatibility method - all models are managed externally."""
        logger.info("unload_all_models called but models are managed externally")
        self.loaded_models.clear()
        await external_ai_manager.close_all_connections()
