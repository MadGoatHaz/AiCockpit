# acp_backend/llm_backends/base.py
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional

# Ensure all necessary Pydantic models are imported for type hints
from acp_backend.models.llm_models import (
    LLMModelInfo, 
    ChatCompletionRequest, 
    ChatCompletionResponse, 
    ChatCompletionChunk
)

class LLMBackend(ABC):
    """Abstract base class for all LLM backends."""

    @abstractmethod
    def get_model_info(self) -> Optional[LLMModelInfo]: # Changed to Optional[LLMModelInfo] for consistency if info can be None
        """Returns detailed information about the loaded model."""
        pass

    @abstractmethod
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Generates a chat completion."""
        pass

    @abstractmethod
    async def stream_chat_completion(self, request: ChatCompletionRequest) -> AsyncGenerator[ChatCompletionChunk, None]:
        """Generates a streaming chat completion."""
        # Ensure the generator yields ChatCompletionChunk or raises an exception
        # This is an abstract method, so the implementation is in subclasses.
        # For type hinting and to make it a valid async generator:
        if False: # pragma: no cover
            yield # type: ignore 

    
    def release(self):
        """
        Releases any resources held by the backend (e.g., unload model from GPU).
        This method should be idempotent.
        """
        pass # Default implementation does nothing
