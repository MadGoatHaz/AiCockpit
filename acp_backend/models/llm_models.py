# acp_backend/models/llm_models.py
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any, Literal

from pydantic import BaseModel, Field

# --- Enums ---
class LLMModelType(Enum):
    LLAMA_CPP = "llama_cpp"
    PIE = "pie"
    MOCK = "mock"

class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class LLMStatus(Enum):
    UNKNOWN = "unknown"
    DISCOVERED = "discovered"
    LOADING = "loading"
    LOADED = "loaded"
    UNLOADING = "unloading"
    UNLOADED = "unloaded"
    ERROR = "error"

# --- LLM Configuration and Data Models ---
class LLMConfig(BaseModel):
    model_id: str = Field(..., description="Unique identifier for this model configuration")
    model_name: str = Field(..., description="User-friendly display name for the model")
    model_path: str = Field(..., description="Path to model file or endpoint URL")
    backend_type: LLMModelType = Field(..., description="Backend type for this model")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Backend-specific parameters")

class LLM(BaseModel):
    config: LLMConfig
    status: LLMStatus = Field(default=LLMStatus.UNKNOWN, description="Current status of the LLM")
    error_message: Optional[str] = Field(None, description="Error message if status is ERROR")

class LLMChatMessage(BaseModel):
    role: MessageRole
    content: str
    name: Optional[str] = None

class LLMChatChoice(BaseModel):
    index: int
    message: LLMChatMessage
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "content_filter", "function_call"]] = None

class LLMUsage(BaseModel):
    prompt_tokens: int = Field(..., ge=0)
    completion_tokens: Optional[int] = Field(None, ge=0)
    total_tokens: int = Field(..., ge=0)

# Canonical name for chat completion objects
class LLMChatCompletion(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex}")
    object: str = Field(default="chat.completion")
    created: int = Field(default_factory=lambda: int(datetime.now(timezone.utc).timestamp()))
    model: str
    choices: List[LLMChatChoice]
    usage: Optional[LLMUsage] = None
    system_fingerprint: Optional[str] = None

# --- API Request Models ---
class LoadLLMRequest(BaseModel): # Kept simplified
    model_id: Optional[str] = Field(None, description="ID of a pre-discovered model config to load.")
    # model_config: Optional[LLMConfig] = Field(None, description="Full configuration for a model to load.") # Still commented

class UnloadLLMRequest(BaseModel):
    model_id: str

class ChatCompletionRequest(BaseModel): # For the API request body
    model_id: str
    messages: List[LLMChatMessage] = Field(..., min_length=1)
    stream: bool = False
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)

# --- API Response Models ---
class DiscoveredLLMConfigResponse(BaseModel):
    configs: List[LLMConfig]

class LLMModelInfo(BaseModel):
    model_id: str
    model_name: str
    backend_type: LLMModelType
    status: LLMStatus
    parameters: Dict[str, Any]

class LoadedLLMsResponse(BaseModel):
    loaded_models: List[LLMModelInfo]

# --- Streaming Specific Models (added based on test_llm_models.py) ---

class LLMChatCompletionChunkDelta(BaseModel):
    content: Optional[str] = None
    role: Optional[MessageRole] = None # Role might appear in the first chunk for some models
    # According to OpenAI spec, tool_calls can also be part of delta.
    # tool_calls: Optional[List[Any]] = None # Placeholder if you add tool usage
    name: Optional[str] = None # If role is tool, name of the tool

class LLMChatCompletionChunkChoice(BaseModel):
    index: int
    delta: LLMChatCompletionChunkDelta
    finish_reason: Optional[Literal["stop", "length", "tool_calls", "content_filter"]] = None
    # logprobs: Optional[Any] = None # If you support log probabilities

class LLMChatCompletionChunk(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl.chunk-{uuid.uuid4().hex}")
    object: str = Field(default="chat.completion.chunk")
    created: int = Field(default_factory=lambda: int(datetime.now(timezone.utc).timestamp()))
    model: str # Model identifier
    choices: List[LLMChatCompletionChunkChoice]
    system_fingerprint: Optional[str] = None # Matches LLMChatCompletion
    # usage: Optional[LLMUsage] = None # Usage typically sent with the last chunk or not at all for chunks
