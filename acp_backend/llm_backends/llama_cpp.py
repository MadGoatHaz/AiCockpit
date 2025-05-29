# acp_backend/llm_backends/llama_cpp.py
import logging
import asyncio
import time
import uuid
from typing import AsyncGenerator, Optional, List, Dict, Any
from pathlib import Path
import queue # For robust streaming
import threading # For robust streaming

try:
    from llama_cpp import Llama, ChatCompletionRequestMessage as LlamaCppChatMessage, ChatCompletionChunk as LlamaCppChatCompletionChunk
    from llama_cpp.llama_types import ChatCompletionRequest as LlamaCppCompletionRequestType # For type checking internal calls
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    Llama = None 
    LlamaCppChatMessage = None 
    LlamaCppChatCompletionChunk = None 
    LlamaCppCompletionRequestType = None
    LLAMA_CPP_AVAILABLE = False
    logging.warning("llama-cpp-python is not installed. LlamaCppBackend will not be available.")

# Corrected imports from canonical llm_models.py
from acp_backend.models.llm_models import (
    LLMModelInfo,
    ChatCompletionRequest as ACPChatCompletionRequest, # This is the request from API
    LLMChatCompletion,       # Was ChatCompletionResponse
    LLMChatMessage,          # Was ChatMessageInput
    LLMChatChoice,           # Was ChatCompletionResponseChoice / ChatCompletionChunkChoice
    MessageRole,             # For constructing LLMChatMessage
    LLMUsage,                # Was UsageInfo
    # LLMConfig, LLMStatus etc. are not directly used in this file's logic but are related
)
# Assuming LLMBackendInterface is the correct base class name from your actual base.py
from acp_backend.llm_backends.base import LLMBackendInterface # Or BaseLLMBackend, or LLMBackend
# from acp_backend.config import AppSettings # If default settings were needed directly

logger = logging.getLogger(__name__)

class LlamaCppBackend(LLMBackendInterface): # Ensure this matches your base class name
    def __init__(
        self, 
        model_path: str, # Changed Path to str to match base, will convert internally
        config_params: Dict[str, Any] # Parameters from LLMConfig
    ):
        super().__init__(model_path=model_path, config_params=config_params) # Call super if inheriting
        if not LLAMA_CPP_AVAILABLE:
            # This check is also in the global scope, but good to have in init too.
            # Log or raise, LLMManager should ideally not instantiate if not available.
            logger.error("llama-cpp-python is not installed. LlamaCppBackend cannot be initialized.")
            raise ImportError("llama-cpp-python is not installed. Cannot use LlamaCppBackend.")
        
        self._model_path_str = model_path # Store original string
        self._model_path_obj = Path(model_path) # Use Path object internally
        
        # Extract parameters from config_params, providing defaults
        self._n_gpu_layers = config_params.get("n_gpu_layers", 0)
        self._n_ctx = config_params.get("n_ctx", 2048)
        self._n_batch = config_params.get("n_batch", 512)
        self._chat_format = config_params.get("chat_format", "llama-2")
        self._verbose = config_params.get("verbose", False) # Or use AppSettings.DEBUG

        self.model_id_str = self._model_path_obj.stem # For use in LLMChatCompletion.model
        self.llm: Optional[Llama] = None
        # self._model_info: Optional[LLMModelInfo] = None # model_info is now part of LLM in LLMManager

        logger.info(f"LlamaCppBackend instance created for model path: {self._model_path_str}. Waiting for load().")

    async def load(self) -> None:
        if self.llm is not None:
            logger.info(f"Model '{self.model_id_str}' appears to be already loaded or load initiated.")
            return

        logger.info(f"Loading LlamaCPP model: {self._model_path_str}...")
        if not self._model_path_obj.exists():
            logger.error(f"Model file not found at {self._model_path_str}")
            raise FileNotFoundError(f"Model file not found at {self._model_path_str}")
        
        try:
            # Llama() is a blocking call, run in thread
            self.llm = await asyncio.to_thread(
                Llama,
                model_path=str(self._model_path_obj),
                n_gpu_layers=self._n_gpu_layers,
                n_ctx=self._n_ctx,
                n_batch=self._n_batch,
                chat_format=self._chat_format,
                verbose=self._verbose,
            )
            logger.info(f"Model '{self.model_id_str}' loaded successfully into LlamaCppBackend.")
        except Exception as e:
            logger.error(f"LlamaCppBackend failed to load model '{self.model_id_str}': {e}", exc_info=True)
            self.llm = None # Ensure llm is None if load fails
            raise # Re-raise the exception

    async def unload(self) -> None:
        if self.llm:
            # The Llama object doesn't have an explicit unload. Deleting it should free resources.
            # Ensure this is thread-safe if unload can be called concurrently with chat_completion
            del self.llm
            self.llm = None
            import gc
            gc.collect()
            logger.info(f"LlamaCPP model {self.model_id_str} resources released (instance deleted).")
        else:
            logger.info(f"LlamaCPP model {self.model_id_str} was not loaded, no unload action taken.")

    def _convert_messages_to_llama_cpp_format(self, messages: List[LLMChatMessage]) -> List[Dict[str,str]]:
        # Llama_cpp expects list of dicts with "role" and "content"
        # LLMChatMessage.role is an Enum, so convert to string value
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]

    # Helper for robust streaming
    def _blocking_llama_cpp_stream_to_queue(
        self,
        llama_cpp_messages: List[Dict[str, str]],
        completion_kwargs: Dict[str, Any],
        output_queue: asyncio.Queue,
        loop: asyncio.AbstractEventLoop
    ):
        try:
            sync_stream_generator = self.llm.create_chat_completion( # type: ignore
                messages=llama_cpp_messages,
                stream=True,
                **completion_kwargs
            )
            for chunk_data_llama_cpp in sync_stream_generator:
                # Put data into the queue, to be consumed by the async generator
                # Use call_soon_threadsafe because this is a sync thread putting to an async queue
                loop.call_soon_threadsafe(output_queue.put_nowait, chunk_data_llama_cpp)
        except Exception as e_stream_thread:
            logger.error(f"LlamaCPP streaming error in worker thread for model {self.model_id_str}: {e_stream_thread}", exc_info=True)
            # Put the exception into the queue so the consumer can know about it
            loop.call_soon_threadsafe(output_queue.put_nowait, e_stream_thread)
        finally:
            # Signal end of stream
            loop.call_soon_threadsafe(output_queue.put_nowait, None)

    async def chat_completion(
        self,
        messages: List[LLMChatMessage],
        stream: bool = False,
        model_id_for_response: Optional[str] = None, # Used to populate the 'model' field in response
        **kwargs: Any,
    ) -> LLMChatCompletion | AsyncGenerator[LLMChatCompletion, None]:
        
        if not self.llm:
            logger.error(f"Model {self.model_id_str} is not loaded or failed to load in LlamaCppBackend.")
            raise RuntimeError(f"Model {self.model_id_str} is not loaded.")

        llama_cpp_messages: List[Dict[str, str]] = self._convert_messages_to_llama_cpp_format(messages)
        
        # Prepare kwargs for llama_cpp by extracting relevant ones from ACPChatCompletionRequest fields
        # or directly from **kwargs if LLMManager passes them through.
        # The ACPChatCompletionRequest fields are: temperature, max_tokens, stop, top_p, top_k, repeat_penalty, grammar
        # These are often passed through **kwargs by LLMManager.
        
        completion_kwargs = {
            "temperature": kwargs.get("temperature", 0.8), # Default from Llama class
            "max_tokens": kwargs.get("max_tokens", None), # Llama class default is None (means -1 for C++)
            "stop": kwargs.get("stop", []),
            "top_p": kwargs.get("top_p", 0.95), # Default from Llama class
            "top_k": kwargs.get("top_k", 40),   # Default from Llama class
            "repeat_penalty": kwargs.get("repeat_penalty", 1.1), # Default from Llama class
            # "grammar": kwargs.get("grammar"), # If LlamaGrammar is passed
        }
        # Filter out None values for kwargs that Llama might not like as None
        completion_kwargs = {k: v for k, v in completion_kwargs.items() if v is not None}
        if "max_tokens" in completion_kwargs and completion_kwargs["max_tokens"] is None:
             completion_kwargs["max_tokens"] = -1 # LlamaCPP uses -1 for unlimited (up to context)

        start_time = time.time()
        response_model_id = model_id_for_response or self.model_id_str

        if stream:
            # For robust streaming: use a thread and an asyncio.Queue
            # The asyncio.Queue will be used to pass chunks from the sync thread to the async generator
            output_queue = asyncio.Queue()
            loop = asyncio.get_event_loop()

            # Start the blocking stream in a separate thread
            streamer_thread = threading.Thread(
                target=self._blocking_llama_cpp_stream_to_queue,
                args=(llama_cpp_messages, completion_kwargs, output_queue, loop)
            )
            streamer_thread.start()

            async def stream_generator() -> AsyncGenerator[LLMChatCompletion, None]:
                try:
                    while True:
                        item = await output_queue.get()
                        if item is None: # Sentinel for end of stream
                            break
                        if isinstance(item, Exception): # Propagate exception from thread
                            raise item
                        
                        # item is chunk_data_llama_cpp (a dict)
                        chunk_data_llama_cpp = item
                        chunk_id = chunk_data_llama_cpp.get("id", f"chatcmpl-{uuid.uuid4().hex}")
                        created_time = chunk_data_llama_cpp.get("created", int(time.time()))
                        
                        chunk_choices: List[LLMChatChoice] = []
                        for choice_data in chunk_data_llama_cpp.get("choices", []):
                            delta_data = choice_data.get("delta", {})
                            delta_role_str = delta_data.get("role")
                            delta_role = MessageRole(delta_role_str) if delta_role_str else None
                            
                            chunk_choices.append(
                                LLMChatChoice(
                                    index=choice_data.get("index", 0),
                                    message=LLMChatMessage(
                                        role=delta_role or MessageRole.ASSISTANT,
                                        content=delta_data.get("content", "")
                                    ),
                                    finish_reason=choice_data.get("finish_reason")
                                )
                            )
                        
                        yield LLMChatCompletion(
                            id=chunk_id,
                            object="chat.completion.chunk",
                            created=created_time,
                            model=response_model_id,
                            choices=chunk_choices,
                            usage=None
                        )
                        # No need for explicit asyncio.sleep here as queue.get() is awaitable
                finally:
                    # Ensure thread is joined if stream_generator exits early (e.g., client disconnect)
                    if streamer_thread.is_alive():
                        # This part is tricky. If the client disconnects, the generator might be
                        # cancelled. The llama_cpp stream might still be running in the thread.
                        # Ideally, llama_cpp would support cancellation.
                        # For now, we log and let the thread finish its current chunk.
                        logger.warning(f"Stream generator for model {self.model_id_str} ending. Thread will complete.")
                        # streamer_thread.join() # Potentially blocking, be careful in async context
                                                # Consider making _blocking_llama_cpp_stream_to_queue check a flag
                                                # or use other inter-thread communication for graceful shutdown.
            return stream_generator()
        else: # Non-streaming
            try:
                # Run blocking call in a thread
                completion_dict = await asyncio.to_thread(
                    self.llm.create_chat_completion, # type: ignore
                    messages=llama_cpp_messages,
                    stream=False,
                    **completion_kwargs
                )
            except Exception as e_nostream:
                logger.error(f"LlamaCPP chat completion error for model {self.model_id_str}: {e_nostream}", exc_info=True)
                raise RuntimeError(f"LlamaCPP chat completion error: {e_nostream}")

            end_time = time.time()
            logger.debug(f"LlamaCPP completion took {end_time - start_time:.2f}s for model {self.model_id_str}")

            choices: List[LLMChatChoice] = []
            for choice_data in completion_dict.get("choices", []):
                message_data = choice_data.get("message", {})
                choices.append(
                    LLMChatChoice(
                        index=choice_data.get("index", 0),
                        message=LLMChatMessage( # Full message here
                            role=MessageRole(message_data.get("role", "assistant")),
                            content=message_data.get("content", "")
                        ),
                        finish_reason=choice_data.get("finish_reason")
                    )
                )
            
            usage_data = completion_dict.get("usage")
            usage_info = None
            if usage_data:
                usage_info = LLMUsage(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0)
                )

            return LLMChatCompletion(
                id=completion_dict.get("id", f"chatcmpl-{uuid.uuid4().hex}"),
                object="chat.completion",
                created=completion_dict.get("created", int(start_time)),
                model=response_model_id,
                choices=choices,
                usage=usage_info
            )

    # release method was from your original, good for explicit cleanup if needed
    # but unload() should handle it now.
    # def release(self):
    #     if self.llm:
    #         del self.llm
    #         self.llm = None
    #         logger.info(f"LlamaCPP model {self.model_id_str} resources released (instance deleted).")
