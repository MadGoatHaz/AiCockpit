import pytest
from pydantic import ValidationError
import datetime
import time
import uuid
from typing import List, Dict, Any, Union, Literal

from acp_backend.models.llm_models import (
    LLMModelInfo, LoadModelRequest, ChatMessageInput, UsageInfo,
    ChatCompletionRequest, ChatCompletionResponseChoice, ChatCompletionResponse,
    ChatCompletionChunkDelta, ChatCompletionChunkChoice, ChatCompletionChunk
)

# --- LLMModelInfo Tests ---
def test_llm_model_info_valid():
    data = {
        "id": "model-123", "name": "Test Model", "loaded": True, "backend": "llama_cpp",
        "path": "/models/test-model.gguf", "size_gb": 7.5, "quantization": "Q4_K_M",
        "architecture": "Llama", "context_length": 4096, "parameters": "7B"
    }
    info = LLMModelInfo(**data)
    for key, value in data.items():
        assert getattr(info, key) == value
    print(f"\n[PASSED] test_llm_model_info_valid")

def test_llm_model_info_minimal():
    data = {"id": "model-min", "name": "Minimal Model", "backend": "pie"}
    info = LLMModelInfo(**data)
    assert info.id == data["id"]
    assert info.loaded is False # Default
    print(f"\n[PASSED] test_llm_model_info_minimal")

def test_llm_model_info_invalid_context_length():
    data = {"id": "ctx-test", "name": "Ctx Model", "backend": "llama_cpp", "context_length": 0}
    with pytest.raises(ValidationError):
        LLMModelInfo(**data)
    print(f"\n[PASSED] test_llm_model_info_invalid_context_length")

# --- LoadModelRequest Tests ---
def test_load_model_request_valid():
    data = {"model_id": "model-to-load", "n_gpu_layers": -1, "n_ctx": 2048, "n_batch": 512}
    req = LoadModelRequest(**data)
    assert req.model_id == "model-to-load"
    assert req.n_gpu_layers == -1
    print(f"\n[PASSED] test_load_model_request_valid")

@pytest.mark.parametrize("field, value, error_type_part", [
    ("n_gpu_layers", -2, "greater_than_equal"),
    ("n_ctx", 0, "greater_than"),
    ("n_batch", 0, "greater_than"),
])
def test_load_model_request_invalid_params(field, value, error_type_part):
    data = {"model_id": "param-test"}
    data[field] = value
    with pytest.raises(ValidationError) as excinfo:
        LoadModelRequest(**data)
    assert error_type_part in excinfo.value.errors()[0]['type']
    print(f"\n[PASSED] test_load_model_request_invalid_params for {field}={value}")

# --- ChatMessageInput Tests ---
def test_chat_message_input_valid():
    msg = ChatMessageInput(role="user", content="Hello!")
    assert msg.role == "user"
    assert msg.content == "Hello!"
    print(f"\n[PASSED] test_chat_message_input_valid")

def test_chat_message_input_invalid_role():
    with pytest.raises(ValidationError):
        ChatMessageInput(role="unknown_role", content="Test") # type: ignore
    print(f"\n[PASSED] test_chat_message_input_invalid_role")

# --- UsageInfo Tests ---
def test_usage_info_valid():
    usage = UsageInfo(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    assert usage.prompt_tokens == 10
    assert usage.total_tokens == 30
    print(f"\n[PASSED] test_usage_info_valid")

def test_usage_info_invalid_tokens():
    with pytest.raises(ValidationError):
        UsageInfo(prompt_tokens=-1, total_tokens=-1)
    print(f"\n[PASSED] test_usage_info_invalid_tokens")

# --- ChatCompletionRequest Tests ---
def test_chat_completion_request_valid_minimal():
    req = ChatCompletionRequest(
        model_id="test-model",
        messages=[ChatMessageInput(role="user", content="Hi")]
    )
    assert req.model_id == "test-model"
    assert req.temperature == 0.7 # Default
    assert req.stream is False # Default
    print(f"\n[PASSED] test_chat_completion_request_valid_minimal")

def test_chat_completion_request_invalid_messages():
    with pytest.raises(ValidationError): # Empty messages list
        ChatCompletionRequest(model_id="test-model", messages=[])
    print(f"\n[PASSED] test_chat_completion_request_invalid_messages")

@pytest.mark.parametrize("field, value, error_type_part", [
    ("temperature", -0.1, "greater_than_equal"),
    ("temperature", 2.1, "less_than_equal"),
    ("max_tokens", 0, "greater_than"),
    ("top_p", -0.1, "greater_than_equal"),
    ("top_p", 1.1, "less_than_equal"),
    ("top_k", -1, "greater_than_equal"),
    ("repeat_penalty", -0.1, "greater_than_equal"),
])
def test_chat_completion_request_invalid_params(field, value, error_type_part):
    data = {"model_id": "param-test-chat", "messages": [ChatMessageInput(role="user", content="Test")]}
    data[field] = value
    with pytest.raises(ValidationError) as excinfo:
        ChatCompletionRequest(**data)
    assert error_type_part in excinfo.value.errors()[0]['type']
    print(f"\n[PASSED] test_chat_completion_request_invalid_params for {field}={value}")

# --- ChatCompletionResponse Tests ---
def test_chat_completion_response_valid():
    choice = ChatCompletionResponseChoice(
        message=ChatMessageInput(role="assistant", content="I'm here."),
        finish_reason="stop"
    )
    resp = ChatCompletionResponse(
        model="test-model-resp",
        choices=[choice],
        usage=UsageInfo(prompt_tokens=5, completion_tokens=3, total_tokens=8)
    )
    assert resp.object == "chat.completion"
    assert resp.choices[0].message.content == "I'm here."
    assert resp.usage.total_tokens == 8
    assert "chatcmpl-" in resp.id
    print(f"\n[PASSED] test_chat_completion_response_valid")

# --- ChatCompletionChunk Tests ---
def test_chat_completion_chunk_valid():
    delta = ChatCompletionChunkDelta(content="Hello")
    choice = ChatCompletionChunkChoice(delta=delta)
    chunk = ChatCompletionChunk(
        id="stream-id-123",
        created=int(time.time()),
        model="test-model-stream",
        choices=[choice]
    )
    assert chunk.object == "chat.completion.chunk"
    assert chunk.choices[0].delta.content == "Hello"
    print(f"\n[PASSED] test_chat_completion_chunk_valid")

def test_chat_completion_chunk_finish_reason():
    delta = ChatCompletionChunkDelta() # Empty delta
    choice = ChatCompletionChunkChoice(delta=delta, finish_reason="length")
    chunk = ChatCompletionChunk(
        id="stream-id-end", created=int(time.time()), model="test-model-stream", choices=[choice]
    )
    assert chunk.choices[0].finish_reason == "length"
    print(f"\n[PASSED] test_chat_completion_chunk_finish_reason")

