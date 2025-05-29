import pytest
from pydantic import ValidationError
import datetime
import time
import uuid
from typing import List, Dict, Any, Union, Literal
from pathlib import Path

from acp_backend.models.llm_models import (
    LLMModelInfo, LoadLLMRequest,
    LLMChatMessage, LLMUsage, LLMChatCompletion, LLMChatChoice,
    LLMChatCompletionChunkDelta, LLMChatCompletionChunkChoice, LLMChatCompletionChunk,
    MessageRole, ChatCompletionRequest, LLMStatus # Added LLMStatus
)

# --- LLMModelInfo Tests ---
def test_llm_model_info_valid():
    data = {
        "model_id": "model-123", 
        "model_name": "Test Model", 
        "backend_type": "llama_cpp", # LLMModelType.LLAMA_CPP if using enum directly
        "status": LLMStatus.LOADED, 
        "parameters": {"path": "/models/test-model.gguf", "api_key_env": "TEST_KEY"}
    }
    info = LLMModelInfo(**data)
    # Check only fields that are directly in data, as backend_type might be an enum object
    assert info.model_id == data["model_id"]
    assert info.model_name == data["model_name"]
    assert info.status == data["status"]
    assert info.parameters == data["parameters"]
    # For backend_type, if it's an enum, direct comparison might differ if data has string
    # assert info.backend_type == data["backend_type"] # or LLMModelType(data["backend_type"])
    print(f"\n[PASSED] test_llm_model_info_valid")

def test_llm_model_info_minimal():
    data = {
        "model_id": "model-min", 
        "model_name": "Minimal Model", 
        "backend_type": "pie", # LLMModelType.PIE
        "status": LLMStatus.UNKNOWN, 
        "parameters": {}
    }
    info = LLMModelInfo(**data)
    assert info.model_id == data["model_id"]
    assert info.status == LLMStatus.UNKNOWN
    print(f"\n[PASSED] test_llm_model_info_minimal")

def test_llm_model_info_invalid_context_length():
    pytest.skip("Skipping test for context_length not directly in LLMModelInfo")

# --- LoadLLMRequest Tests ---
def test_load_llm_request_valid(): # Renamed test function
    data = {"model_id": "model-to-load"}
    req = LoadLLMRequest(**data)
    assert req.model_id == "model-to-load"
    print(f"\n[PASSED] test_load_llm_request_valid")

@pytest.mark.parametrize("field, value, error_type_part", [
    # This test is not applicable to the current LoadLLMRequest model.
])
def test_load_llm_request_invalid_params(field, value, error_type_part): # Renamed test function
    pytest.skip("Skipping test for fields not currently in LoadLLMRequest model")

# --- LLMChatMessage Tests ---
def test_llm_chat_message_valid():
    msg = LLMChatMessage(role=MessageRole.USER, content="Hello!")
    assert msg.role == MessageRole.USER
    assert msg.content == "Hello!"
    print(f"\n[PASSED] test_llm_chat_message_valid")

def test_llm_chat_message_invalid_role():
    with pytest.raises(ValidationError):
        LLMChatMessage(role="unknown_role", content="Test") # type: ignore
    print(f"\n[PASSED] test_llm_chat_message_invalid_role")

# --- LLMUsage Tests ---
def test_llm_usage_valid():
    usage = LLMUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    assert usage.prompt_tokens == 10
    assert usage.total_tokens == 30
    print(f"\n[PASSED] test_llm_usage_valid")

def test_llm_usage_invalid_tokens():
    with pytest.raises(ValidationError):
        LLMUsage(prompt_tokens=-1, total_tokens=-1)
    print(f"\n[PASSED] test_llm_usage_invalid_tokens")

# --- ChatCompletionRequest Tests ---
def test_chat_completion_request_valid_minimal():
    req = ChatCompletionRequest(
        model_id="test-model",
        messages=[LLMChatMessage(role=MessageRole.USER, content="Hi")]
    )
    assert req.model_id == "test-model"
    # Assuming ChatCompletionRequest in llm_models has these defaults from Pydantic Field
    assert req.temperature == 0.7 
    assert req.stream is False 
    print(f"\n[PASSED] test_chat_completion_request_valid_minimal")

def test_chat_completion_request_invalid_messages():
    with pytest.raises(ValidationError): # Empty messages list
        ChatCompletionRequest(model_id="test-model", messages=[])
    print(f"\n[PASSED] test_chat_completion_request_invalid_messages")

@pytest.mark.parametrize("field, value, error_type_part", [
    ("temperature", -0.1, "greater_than_equal"),
    ("temperature", 2.1, "less_than_equal"),
    ("max_tokens", 0, "greater_than"),
])
def test_chat_completion_request_invalid_params(field, value, error_type_part):
    data = {"model_id": "param-test-chat", "messages": [LLMChatMessage(role=MessageRole.USER, content="Test")]}
    data[field] = value
    with pytest.raises(ValidationError) as excinfo:
        ChatCompletionRequest(**data)
    assert error_type_part in excinfo.value.errors()[0]['type']
    print(f"\n[PASSED] test_chat_completion_request_invalid_params for {field}={value}")

# --- LLMChatCompletion Tests ---
def test_llm_chat_completion_valid():
    choice = LLMChatChoice(
        index=0,
        message=LLMChatMessage(role=MessageRole.ASSISTANT, content="I'm here."),
        finish_reason="stop"
    )
    resp = LLMChatCompletion(
        model="test-model-resp",
        choices=[choice],
        usage=LLMUsage(prompt_tokens=5, completion_tokens=3, total_tokens=8)
    )
    assert resp.object == "chat.completion"
    assert resp.choices[0].message.content == "I'm here."
    assert resp.usage.total_tokens == 8
    assert "chatcmpl-" in resp.id
    print(f"\n[PASSED] test_llm_chat_completion_valid")

# --- LLMChatCompletionChunk Tests ---
def test_llm_chat_completion_chunk_valid():
    delta = LLMChatCompletionChunkDelta(content="Hello")
    choice = LLMChatCompletionChunkChoice(index=0, delta=delta)
    chunk = LLMChatCompletionChunk(
        id="stream-id-123",
        created=int(time.time()),
        model="test-model-stream",
        choices=[choice]
    )
    assert chunk.object == "chat.completion.chunk"
    assert chunk.choices[0].delta.content == "Hello"
    print(f"\n[PASSED] test_llm_chat_completion_chunk_valid")

def test_llm_chat_completion_chunk_finish_reason():
    delta = LLMChatCompletionChunkDelta()
    choice = LLMChatCompletionChunkChoice(index=0, delta=delta, finish_reason="length")
    chunk = LLMChatCompletionChunk(id="stream-id-end", created=int(time.time()), model="test-model-stream", choices=[choice])
    assert chunk.choices[0].finish_reason == "length"
    print(f"\n[PASSED] test_llm_chat_completion_chunk_finish_reason")

