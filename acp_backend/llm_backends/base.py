# acp_backend/llm_backends/base.py
import logging
from abc import ABC, abstractmethod
from typing import List, AsyncGenerator, Optional, Dict, Any

# Using canonical model names from the definitive llm_models.py
from acp_backend.models.llm_models import (
    LLMChatMessage,
    LLMChatCompletion,    # Canonical name for completion object
    LLMModelInfo,
    LLMConfig,
    # LoadLLMRequest,     # Not typically used by the backend interface itself
    # ChatCompletionRequest # The backend interface takes decomposed args
)

logger = logging.getLogger(__name__)

class LLMBackendInterface(ABC):
    """
    Abstract base class for LLM backend implementations.
    """

    def __init__(self, model_path: str, config_params: Dict[str, Any]):
        """
        Initialize the backend.

        Args:
            model_path: Path or identifier for the model.
            config_params: Backend-specific configuration parameters from LLMConfig's 'parameters' field.
        """
        self.model_path = model_path
        self.config_params = config_params
        logger.info(f"LLMBackendInterface initialized for model path: {model_path} with params: {config_params}")

    @abstractmethod
    async def load(self) -> None:
        """
        Load the model into memory.
        Implementations should handle their specific loading logic.
        This method should make the backend ready for chat_completion calls.
        """
        pass

    @abstractmethod
    async def unload(self) -> None:
        """
        Unload the model from memory and release resources.
        (Implement if explicit cleanup is needed beyond object deletion)
        """
        pass

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[LLMChatMessage],
        stream: bool = False,
        model_id_for_response: Optional[str] = None, # model_id to put in the response object
        **kwargs: Any, # For backend-specific parameters like temperature, max_tokens, etc.
    ) -> LLMChatCompletion | AsyncGenerator[LLMChatCompletion, None]:
        """
        Generate a chat completion.
        The 'model' field in the returned LLMChatCompletion object should be populated
        using model_id_for_response or an internally known model ID.
        """
        pass
