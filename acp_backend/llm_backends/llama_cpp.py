# acp_backend/llm_backends/llama_cpp.py
import logging
import asyncio
import time
import uuid
from typing import AsyncGenerator, Optional, List, Dict, Any
from pathlib import Path

try:
    from llama_cpp import Llama, ChatCompletionRequestMessage as LlamaCppChatMessage, ChatCompletionChunk as LlamaCppChatCompletionChunk
    # Correctly import the type for the main request object if needed for type checking internal calls
    from llama_cpp.llama_types import ChatCompletionRequest as LlamaCppCompletionRequest 
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    Llama = None # type: ignore
    LlamaCppChatMessage = None # type: ignore
    LlamaCppChatCompletionChunk = None # type: ignore
    LlamaCppCompletionRequest = None # type: ignore
    LLAMA_CPP_AVAILABLE = False
    logging.warning("llama-cpp-python is not installed. LlamaCppBackend will not be available.")

from acp_backend.models.llm_models import (
    LLMModelInfo, ChatCompletionRequest as ACPChatCompletionRequest,
    ChatCompletionResponse, ChatCompletionChunk, ChatMessageInput,
    ChatCompletionResponseChoice, ChatCompletionChunkChoice, ChatCompletionChunkDelta,
    UsageInfo
)
# Corrected import: LLMBackend instead of BaseLLMBackend
from acp_backend.llm_backends.base import LLMBackend 
from acp_backend.config import Settings # For default settings if needed directly

logger = logging.getLogger(__name__)

class LlamaCppBackend(LLMBackend):
    def __init__(
        self, 
        model_path: Path,
        n_gpu_layers: int = 0,
        n_ctx: int = 2048,
        n_batch: int = 512,
        chat_format: str = "llama-2",
        verbose: bool = False,
    ):
        if not LLAMA_CPP_AVAILABLE:
            raise ImportError("llama-cpp-python is not installed. Cannot use LlamaCppBackend.")
        
        self._model_path = model_path
        self._n_gpu_layers = n_gpu_layers
        self._n_ctx = n_ctx
        self._n_batch = n_batch
        self._chat_format = chat_format
        self._verbose = verbose

        self.model_id = model_path.stem
        self.llm: Optional[Llama] = None
        self._model_info: Optional[LLMModelInfo] = None
        
        try:
            self._load_model_instance()
            logger.info(f"LlamaCppBackend initialized for model: {self.model_id}")
        except Exception as e:
            # Log the error but allow the object to be created, get_model_info will report not loaded.
            logger.error(f"LlamaCppBackend failed to load model '{self.model_id}' during init: {e}", exc_info=True)
            self._model_info = LLMModelInfo(
                id=self.model_id, name=self.model_id, path=str(self._model_path), loaded=False, backend="llama_cpp"
            )


    def _load_model_instance(self):
        # This is a blocking call, should be wrapped if called from async context directly
        # However, __init__ is synchronous.
        if not self._model_path.exists():
            raise FileNotFoundError(f"Model file not found at {self._model_path}")
        
        self.llm = Llama(
            model_path=str(self._model_path),
            n_gpu_layers=self._n_gpu_layers,
            n_ctx=self._n_ctx,
            n_batch=self._n_batch,
            chat_format=self._chat_format,
            verbose=self._verbose,
        )
        size_gb = round(self._model_path.stat().st_size / (1024**3), 2) if self._model_path.exists() else None
        
        self._model_info = LLMModelInfo(
            id=self.model_id,
            name=self.model_id, 
            path=str(self._model_path.resolve()),
            size_gb=size_gb,
            quantization=self._extract_quant_from_path(self._model_path.name), 
            loaded=True,
            backend="llama_cpp",
            context_length=self.llm.n_ctx() if self.llm else self._n_ctx,
        )
        logger.info(f"Model '{self.model_id}' loaded into LlamaCppBackend.")

    def _extract_quant_from_path(self, filename: str) -> Optional[str]:
        name_lower = filename.lower()
        parts = name_lower.split('.')[0].split('-') 
        for part in reversed(parts):
            if part.startswith('q') and ('k_' in part or '0' in part or '1' in part or 's' == part[-1]): # common quants
                # Attempt to return a standardized format if possible
                return part.upper().replace("_", "") # e.g. Q4KM
        return None

    def get_model_info(self) -> Optional[LLMModelInfo]:
        if self.llm and self._model_info:
            self._model_info.context_length = self.llm.n_ctx()
            self._model_info.loaded = True 
            return self._model_info
        # If LLM object isn't there but path exists, provide basic info
        elif self._model_path.exists(): 
            if self._model_info and not self._model_info.loaded: # Was attempted but failed
                return self._model_info
            # Construct basic info if not even attempted
            try:
                size_gb = round(self._model_path.stat().st_size / (1024**3), 2)
                return LLMModelInfo(
                    id=self._model_path.stem,
                    name=self._model_path.stem,
                    path=str(self._model_path.resolve()),
                    size_gb=size_gb,
                    quantization=self._extract_quant_from_path(self._model_path.name),
                    loaded=False, 
                    backend="llama_cpp",
                    context_length=self._n_ctx 
                )
            except Exception as e:
                logger.error(f"Could not stat model file {self._model_path} for info: {e}")
                return LLMModelInfo(id=self._model_path.stem, name=self._model_path.stem, loaded=False, backend="llama_cpp")
        return None


    def _convert_messages_to_llama_cpp_format(self, messages: List[ChatMessageInput]) -> List[Dict[str,str]]:
        # Llama_cpp expects list of dicts, not Pydantic models directly for messages
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    async def chat_completion(self, request: ACPChatCompletionRequest) -> ChatCompletionResponse:
        if not self.llm:
            raise RuntimeError(f"Model {self.model_id} is not loaded or failed to load.")

        llama_cpp_messages = self._convert_messages_to_llama_cpp_format(request.messages)
        
        start_time = time.time()
        
        def _create_completion_sync():
            # Ensure LlamaCppCompletionRequest is the correct type for the call
            # The create_chat_completion method itself takes kwargs that match the fields
            # of the LlamaCppCompletionRequest Pydantic model.
            return self.llm.create_chat_completion( # type: ignore
                messages=llama_cpp_messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens if request.max_tokens is not None else -1, # -1 for llama-cpp means until eos or n_ctx
                stop=request.stop,
                top_p=request.top_p if request.top_p is not None else 1.0, 
                top_k=request.top_k if request.top_k is not None else 40,   
                repeat_penalty=request.repeat_penalty if request.repeat_penalty is not None else 1.1, 
                grammar=request.grammar if request.grammar else None,
                stream=False 
            )
        
        try:
            completion = await asyncio.to_thread(_create_completion_sync)
        except Exception as e:
            logger.error(f"LlamaCPP chat completion error for model {self.model_id}: {e}", exc_info=True)
            raise RuntimeError(f"LlamaCPP chat completion error: {e}")

        end_time = time.time()
        logger.debug(f"LlamaCPP completion took {end_time - start_time:.2f}s for model {self.model_id}")

        choices: List[ChatCompletionResponseChoice] = []
        for choice_data in completion.get("choices", []): # type: ignore
            message_data = choice_data.get("message", {})
            choices.append(
                ChatCompletionResponseChoice(
                    index=choice_data.get("index", 0),
                    message=ChatMessageInput(
                        role=message_data.get("role", "assistant"),
                        content=message_data.get("content", "")
                    ),
                    finish_reason=choice_data.get("finish_reason")
                )
            )
        
        usage_data = completion.get("usage") # type: ignore
        usage_info = None
        if usage_data:
            usage_info = UsageInfo(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0)
            )

        return ChatCompletionResponse(
            id=completion.get("id", f"chatcmpl-{uuid.uuid4()}"), # type: ignore
            object="chat.completion",
            created=completion.get("created", int(start_time)), # type: ignore
            model=completion.get("model", self.model_id), # type: ignore
            choices=choices,
            usage=usage_info
        )

    async def stream_chat_completion(self, request: ACPChatCompletionRequest) -> AsyncGenerator[ChatCompletionChunk, None]:
        if not self.llm:
            raise RuntimeError(f"Model {self.model_id} is not loaded or failed to load.")

        llama_cpp_messages = self._convert_messages_to_llama_cpp_format(request.messages)
        
        def _get_stream_generator_sync():
            return self.llm.create_chat_completion( # type: ignore
                messages=llama_cpp_messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens if request.max_tokens is not None else -1,
                stop=request.stop,
                top_p=request.top_p if request.top_p is not None else 1.0,
                top_k=request.top_k if request.top_k is not None else 40,
                repeat_penalty=request.repeat_penalty if request.repeat_penalty is not None else 1.1,
                grammar=request.grammar if request.grammar else None,
                stream=True
            )

        try:
            # The generator itself is created synchronously
            stream_completion_generator = _get_stream_generator_sync()

            # Iterating over the generator items might be blocking
            for chunk_data_llama_cpp in stream_completion_generator:
                # Wrap the processing of each chunk if it's CPU bound,
                # or if next(generator) is blocking.
                # For llama.cpp, next() on the stream is indeed blocking.
                
                # This part needs to be non-blocking for the async generator
                # One way is to run the blocking iteration in a thread,
                # but that makes yielding back to the async event loop complex.
                # A simpler way for now if the blocking per chunk is small:
                # (This is not ideal for true async, but common for wrapping sync generators)

                # Re-evaluate if this needs to be run in a thread per chunk or if the generator itself handles yielding control.
                # llama-cpp-python's stream generator yields dicts.
                
                if isinstance(chunk_data_llama_cpp, dict):
                    chunk_id = chunk_data_llama_cpp.get("id", f"chatcmpl-{uuid.uuid4()}")
                    created_time = chunk_data_llama_cpp.get("created", int(time.time()))
                    model_name = chunk_data_llama_cpp.get("model", self.model_id)
                    
                    chunk_choices: List[ChatCompletionChunkChoice] = []
                    for choice_data in chunk_data_llama_cpp.get("choices", []):
                        delta_data = choice_data.get("delta", {})
                        chunk_choices.append(
                            ChatCompletionChunkChoice(
                                index=choice_data.get("index", 0),
                                delta=ChatCompletionChunkDelta(
                                    role=delta_data.get("role"), # Can be None
                                    content=delta_data.get("content") # Can be None
                                ),
                                finish_reason=choice_data.get("finish_reason") # Can be None
                            )
                        )
                    
                    yield ChatCompletionChunk(
                        id=chunk_id,
                        object="chat.completion.chunk",
                        created=created_time,
                        model=model_name,
                        choices=chunk_choices
                    )
                else:
                    logger.warning(f"Unexpected chunk type from LlamaCPP stream: {type(chunk_data_llama_cpp)}")
                
                await asyncio.sleep(0.001) # Yield control to event loop briefly

        except Exception as e:
            logger.error(f"LlamaCPP streaming chat completion error for model {self.model_id}: {e}", exc_info=True)
            raise RuntimeError(f"LlamaCPP streaming error: {e}")


    def release(self):
        if self.llm:
            del self.llm
            self.llm = None
            if self._model_info:
                self._model_info.loaded = False
            logger.info(f"LlamaCPP model {self.model_id} resources released (instance deleted).")
