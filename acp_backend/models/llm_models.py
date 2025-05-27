# acp_backend/models/llm_models.py
from pydantic import BaseModel, Field, ConfigDict 
from typing import List, Optional, Dict, Any, Union, Literal
import time 
import uuid 

class LLMModelInfo(BaseModel):
    model_config = ConfigDict(extra="forbid") 

    id: str = Field(..., description="Unique identifier for the model.")
    name: str = Field(..., description="Display name of the model.")
    path: Optional[str] = Field(None, description="Filesystem path to the model file, if applicable.")
    size_gb: Optional[float] = Field(None, ge=0, description="Size of the model file in GB. Must be non-negative if set.")
    quantization: Optional[str] = Field(None, description="Quantization type (e.g., 'Q4_K_M', 'F16').")
    loaded: bool = Field(False, description="Indicates if the model is currently loaded in memory.")
    backend: str = Field(..., description="Identifier of the backend managing this model.")
    architecture: Optional[str] = Field(None, description="Model architecture (e.g., 'Llama', 'Mistral').")
    context_length: Optional[int] = Field(None, gt=0, description="Maximum context length. Must be positive if set.")
    parameters: Optional[str] = Field(None, description="Number of parameters (e.g., '7B', '70B').")

class LoadModelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid") 

    model_id: Optional[str] = Field(None, description="ID of a previously discovered model to load.")
    model_path: Optional[str] = Field(None, description="Path to the GGUF model file.")
    n_gpu_layers: Optional[int] = Field(None, ge=-1, description="Layers to offload to GPU (-1 for all). Llama.cpp specific.")
    n_ctx: Optional[int] = Field(None, gt=0, description="Context size override. Must be positive. Llama.cpp specific.")
    n_batch: Optional[int] = Field(None, gt=0, description="Batch size for prompt processing. Must be positive. Llama.cpp specific.")
    chat_format: Optional[str] = Field(None, description="Chat format string (e.g., 'llama-2'). Llama.cpp specific.")

class ChatMessageInput(BaseModel):
    model_config = ConfigDict(extra="forbid") 

    role: Literal["system", "user", "assistant"] = Field(..., description="Role of the message sender.")
    content: str = Field(..., description="Content of the message.")

class UsageInfo(BaseModel):
    model_config = ConfigDict(extra="forbid") 

    prompt_tokens: int = Field(..., ge=0)
    completion_tokens: Optional[int] = Field(None, ge=0)
    total_tokens: int = Field(..., ge=0)

class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid") 

    model_id: str = Field(..., description="ID of the loaded LLM model to use.")
    messages: List[ChatMessageInput] = Field(..., min_length=1, description="Conversation history.")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Controls randomness.")
    max_tokens: Optional[int] = Field(512, gt=0, description="Max tokens to generate. Must be positive if set.")
    stream: bool = Field(False, description="If True, stream response via SSE.")
    stop: Optional[Union[str, List[str]]] = Field(None, description="Stop sequence(s).")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Nucleus sampling cutoff.")
    top_k: Optional[int] = Field(None, ge=0, description="Consider k most likely tokens.")
    repeat_penalty: Optional[float] = Field(None, ge=0.0, description="Penalty for repeating tokens (1.0 is neutral).")
    grammar: Optional[str] = Field(None, description="GBNF grammar string (Llama.cpp specific).")

class ChatCompletionResponseChoice(BaseModel):
    model_config = ConfigDict(extra="forbid") 

    index: int = Field(0, ge=0)
    message: ChatMessageInput 
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "content_filter", "function_call", "error"]] = Field(None, description="Reason generation stopped.")

class ChatCompletionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid") 

    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4()}", description="Unique completion ID.")
    object: Literal["chat.completion"] = Field("chat.completion", description="Object type.")
    created: int = Field(default_factory=lambda: int(time.time()), description="Unix timestamp of creation.")
    model: str = Field(..., description="ID of the model used.")
    choices: List[ChatCompletionResponseChoice] = Field(..., min_length=1)
    usage: Optional[UsageInfo] = None

class ChatCompletionChunkDelta(BaseModel):
    model_config = ConfigDict(extra="forbid") 

    role: Optional[Literal["system", "user", "assistant"]] = None
    content: Optional[str] = None 

class ChatCompletionChunkChoice(BaseModel):
    model_config = ConfigDict(extra="forbid") 

    index: int = Field(0, ge=0)
    delta: ChatCompletionChunkDelta
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "content_filter", "function_call", "error"]] = Field(None, description="Reason generation stopped (final chunk).")

class ChatCompletionChunk(BaseModel):
    model_config = ConfigDict(extra="forbid") 

    id: str = Field(..., description="ID of the overall stream.")
    object: Literal["chat.completion.chunk"] = Field("chat.completion.chunk", description="Object type.")
    created: int = Field(..., description="Timestamp of creation.")
    model: str = Field(..., description="ID of the model used.")
    choices: List[ChatCompletionChunkChoice] 
