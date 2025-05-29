# tests/integration/test_streaming_endpoints.py
import pytest
import httpx
import json
import asyncio
import sys 
import uuid 
import datetime
from typing import List, AsyncGenerator, Optional, Dict, Any 
from unittest import mock 
import anyio 

from fastapi import status

# Import the specific Event class used by anyio's asyncio backend
from anyio._backends._asyncio import Event as AsyncioAnyioEvent

from acp_backend.models.llm_models import (
    ChatCompletionRequest, 
    LLMChatCompletionChunk,
    LLMChatMessage,
    LLMChatCompletionChunkDelta,
    LLMChatCompletionChunkChoice
)
from acp_backend.models.agent_models import ( 
    RunAgentRequest,
    AgentOutputChunk,
    AgentConfig
)
from acp_backend.core.llm_manager import LLMManager 
from acp_backend.core.agent_executor import AgentExecutor as AgentExecutorClass 
from acp_backend.core.agent_config_handler import AgentConfigHandler as AgentConfigHandlerClass

# Module where sse-starlette's anyio.Event will be resolved
SSE_STARLETTE_MODULE_PATH = "sse_starlette.sse" 

pytestmark = pytest.mark.asyncio

async def mock_chat_completion_stream_generator(
    request: ChatCompletionRequest,
    num_chunks: int = 1 # Default to 1 for simplicity
) -> AsyncGenerator[Dict[str, Any], None]:
    print(f"\n[MOCK_GENERATOR] mock_chat_completion_stream_generator called for: {request.messages[-1].content}")
    base_id = f"chatcmpl-stream-mock-{uuid.uuid4()}" # Unique ID
    model_id_to_return = request.model_id
    
    # Create a single chunk
    chunk_content = "Test Stream Chunk 1"
    delta = LLMChatCompletionChunkDelta(content=chunk_content, role="assistant") # Role for first chunk
    choice = LLMChatCompletionChunkChoice(index=0, delta=delta, finish_reason="stop") # Single chunk, so finish
    current_time_int_s = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    chunk = LLMChatCompletionChunk(
        id=base_id, 
        object="chat.completion.chunk", 
        created=current_time_int_s, 
        model=model_id_to_return, 
        choices=[choice]
    )
    
    print(f"[MOCK_GENERATOR] Yielding chunk: {chunk.model_dump_json(indent=2)}")
    yield chunk # Yield the Pydantic model object directly
    print("[MOCK_GENERATOR] Finished mock_chat_completion_stream_generator.")

@pytest.fixture
def patch_anyio_event_for_sse(monkeypatch):
    """
    Patches anyio.Event specifically for the sse_starlette.sse module
    to ensure it uses an event compatible with the current test loop.
    Also resets the AppStatus.should_exit_event to ensure it's fresh.
    """
    from sse_starlette.sse import AppStatus  # Import here

    # Explicitly reset the global event before patching and test execution
    AppStatus.should_exit_event = None

    original_anyio_event = anyio.Event
    
    class PatchedAsyncioEventForSSE(AsyncioAnyioEvent):
        def __init__(self):
            # Call the superclass __init__. For AsyncioAnyioEvent, this
            # executes: self._event = asyncio.Event()
            # This ensures the event is created using asyncio's default mechanism
            # for associating with the current event loop.
            super().__init__()

    # Patch where sse_starlette.sse would look for anyio.Event
    # This assumes sse_starlette.sse does 'import anyio' and then uses 'anyio.Event'
    # or 'from anyio import Event' and it gets aliased/used as anyio.Event in its scope.
    # Based on sse-starlette source, it uses `anyio.Event()`.
    # If sse_starlette.sse has `import anyio` at its module level, then this is the path:
    monkeypatch.setattr(f"{SSE_STARLETTE_MODULE_PATH}.anyio.Event", PatchedAsyncioEventForSSE)
    
    yield  # Test runs here
    
    # Revert the patch
    monkeypatch.setattr(f"{SSE_STARLETTE_MODULE_PATH}.anyio.Event", original_anyio_event)
    # Clean up the global event after the test
    AppStatus.should_exit_event = None


async def test_stream_llm_chat_completions(
    test_client: httpx.AsyncClient, 
    test_llm_manager: mock.Mock,
    patch_anyio_event_for_sse # Apply the patch
):
    test_llm_manager.stream_process_chat_completion.side_effect = mock_chat_completion_stream_generator
    model_id_to_test = "mock-llm" 
    chat_request_payload = ChatCompletionRequest(model_id=model_id_to_test, messages=[LLMChatMessage(role="user", content="Hello stream!")], stream=True, max_tokens=50)
    received_chunks: List[LLMChatCompletionChunk] = []
    
    async with test_client.stream("POST", "/llm/chat/completions", json=chat_request_payload.model_dump(mode="json")) as response:
        assert response.status_code == status.HTTP_200_OK
        assert "text/event-stream" in response.headers.get("content-type", "")
        
        full_response_text = ""
        async for text_chunk in response.aiter_text():
            full_response_text += text_chunk
        
        print(f"[TEST_DEBUG] Full response text (repr):\n{repr(full_response_text)}") # DEBUG with repr

        buffer = full_response_text
        # Use \r\n\r\n as separator, consistent with SSE spec and observed output
        while "\r\n\r\n" in buffer:
            message, buffer = buffer.split("\r\n\r\n", 1)
            data_payload_str = None
            event_field_from_sse = None
            # Split lines within a message by \r\n or \n for flexibility
            lines_in_message = message.replace("\r\n", "\n").split('\n')
            print(f"[TEST_DEBUG] SSE Message Block (lines: {lines_in_message}):\n{message}")
            for line in lines_in_message:
                if line.startswith("data:"):
                    data_payload_str = line[len("data:"):].strip()
                elif line.startswith("event:"):
                    event_field_from_sse = line[len("event:"):].strip()
            
            print(f"[TEST_DEBUG] Parsed Event: '{event_field_from_sse}', Data Present: {bool(data_payload_str)}, Data: '{data_payload_str}'") # RE-ADD & ENHANCE FOR DEBUGGING

            if event_field_from_sse == "error":
                pytest.fail(f"Server sent error event: data: {data_payload_str}")
            elif event_field_from_sse == "eos":
                print(f"Received EOS event with data: {data_payload_str}")
                try:
                    eos_data = json.loads(data_payload_str)
                    assert "message" in eos_data
                except (json.JSONDecodeError, AssertionError) as e:
                    pytest.fail(f"Invalid EOS event data: {data_payload_str}. Error: {e}")
            elif data_payload_str: # Assumes "message" type or None
                try:
                    chunk_obj = LLMChatCompletionChunk.model_validate_json(data_payload_str)
                    received_chunks.append(chunk_obj)
                except Exception as e:
                    pytest.fail(f"Failed to validate ChatCompletionChunk: {repr(data_payload_str)}. Error: {e}")
        
        # Removed the separate "if buffer.strip():" block as it's covered by processing full_response_text
            
    assert len(received_chunks) == 1, f"Expected 1 chunk, got {len(received_chunks)}. Chunks: {received_chunks}"
    if received_chunks: # Additional check for content if needed
        assert received_chunks[0].choices[0].delta.content == "Test Stream Chunk 1"
    test_llm_manager.stream_process_chat_completion.assert_called_once()


async def mock_agent_output_stream_generator(
    request: RunAgentRequest, 
    num_outputs: int = 3 
) -> AsyncGenerator[AgentOutputChunk, None]:
    run_id = f"agent-run-mock-{uuid.uuid4()}"
    event_types = ["status", "step", "output"] 
    
    chunk_start = AgentOutputChunk(run_id=run_id, type="status", data={"message": "Agent task started."})
    yield chunk_start # Yield Pydantic model directly

    for i in range(num_outputs):
        event_type = event_types[i % len(event_types)]
        data_payload: Dict[str, Any]
        if event_type == "status": 
            data_payload = {"message": f"Processing step {i+1}"}
        elif event_type == "step": 
            data_payload = {"step_name": f"Action {i+1}", "details": f"Performing action {i+1} for '{request.input_prompt}'."}
        else: 
            data_payload = {"content": f"Agent output chunk {i+1} for '{request.input_prompt}'."}
        
        chunk_loop = AgentOutputChunk(run_id=run_id, type=event_type, data=data_payload)
        yield chunk_loop # Yield Pydantic model directly
    
    chunk_end = AgentOutputChunk(run_id=run_id, type="status", data={"message": "Agent task completed.", "final": True})
    yield chunk_end # Yield Pydantic model directly


async def test_stream_agent_task_outputs(
    test_client: httpx.AsyncClient,
    test_agent_config_handler: AgentConfigHandlerClass,
    test_llm_manager: mock.Mock,
    patch_anyio_event_for_sse # Apply the patch
):
    agent_id = f"streaming-agent-{uuid.uuid4()}"
    llm_model_id_for_agent = "mock-llm" 

    agent_conf = AgentConfig(
        agent_id=agent_id,
        name="My Streaming Agent",
        agent_type="TestStreamer",
        llm_model_id=llm_model_id_for_agent, 
        system_prompt="You are a helpful streaming agent."
    )
    await test_agent_config_handler.save_global_agent_config(agent_conf)
    
    with mock.patch.object(AgentExecutorClass, 'stream_agent_task_outputs', side_effect=mock_agent_output_stream_generator) as mock_stream_method:
        run_request = RunAgentRequest(
            agent_id=agent_id,
            input_prompt="Hello streaming agent!"
        )

        received_events_data: List[AgentOutputChunk] = []
        expected_num_events = 1 + 3 + 1 

        try:
            async with test_client.stream("POST", "/agents/run/stream", json=run_request.model_dump(mode="json")) as response:
                assert response.status_code == status.HTTP_200_OK, f"Expected 200, got {response.status_code}. Response text: {await response.aread()}"
                assert "text/event-stream" in response.headers.get("content-type", "")

                buffer = ""
                await asyncio.sleep(0.01) # Allow event loop to switch tasks, slightly longer
                async for text_chunk in response.aiter_text():
                    print(f"DEBUG_TEST_AGENT_STREAM: Received text_chunk: {repr(text_chunk)}", file=sys.stderr) # Corrected Indentation
                    buffer += text_chunk.replace('\r\n', '\n').replace('\r', '\n')
                while "\n\n" in buffer:
                        message, buffer = buffer.split("\n\n", 1)
                        event_type_from_sse = None
                        for line in message.splitlines():
                            if line.startswith("data:"):
                                data_payload_str = line[len("data:"):].strip()
                            elif line.startswith("event:"):
                                event_type_from_sse = line[len("event:"):].strip()
                        
                        if event_type_from_sse == "error" and data_payload_str:
                            pytest.fail(f"Server sent error event: data: {data_payload_str}")

                        if data_payload_str:
                            # For agent outputs, all events should be parsable as AgentOutputChunk
                            # The 'eos' event is not standard here, errors are handled by the 'error' event type.
                            try:
                                data_obj = AgentOutputChunk.model_validate_json(data_payload_str)
                                # Check if the event type from SSE matches the type in the data, if available
                                if event_type_from_sse and hasattr(data_obj, 'type') and event_type_from_sse != data_obj.type:
                                    print(f"Warning: SSE event type '{event_type_from_sse}' mismatches data type '{data_obj.type}'")
                                received_events_data.append(data_obj)
                            except Exception as e:
                                pytest.fail(f"Failed to validate AgentOutputChunk from SSE event: {repr(data_payload_str)}. Error: {e}")
        except Exception as client_exc: 
            pytest.fail(f"Exception during test_client.stream or SSE iteration: {client_exc}")

        # After the loop, process any remaining data in the buffer
        if buffer.strip():
            message = buffer
            data_payload_str = None
            event_type_from_sse = None
            for line in message.splitlines():
                if line.startswith("data:"):
                    data_payload_str = line[len("data:"):].strip()
                elif line.startswith("event:"):
                    event_type_from_sse = line[len("event:"):].strip()

            if event_type_from_sse == "error" and data_payload_str:
                pytest.fail(f"Server sent error event from remaining buffer: data: {data_payload_str}")
            
            if data_payload_str:
                try:
                    data_obj = AgentOutputChunk.model_validate_json(data_payload_str)
                    if event_type_from_sse and hasattr(data_obj, 'type') and event_type_from_sse != data_obj.type:
                         print(f"Warning: SSE event type '{event_type_from_sse}' (remaining buffer) mismatches data type '{data_obj.type}'")
                    received_events_data.append(data_obj)
                except Exception as e:
                    pytest.fail(f"Failed to validate AgentOutputChunk from SSE event (remaining buffer): {repr(data_payload_str)}. Error: {e}")

        assert len(received_events_data) == expected_num_events, f"Expected {expected_num_events} agent events, got {len(received_events_data)}. Events: {received_events_data}"

        assert received_events_data[0].type == "status"
        assert received_events_data[0].data["message"] == "Agent task started."
        
        assert received_events_data[1].type == "status" 
        assert received_events_data[1].data["message"] == "Processing step 1"
        
        assert received_events_data[2].type == "step"
        expected_detail_string_event2 = f"Performing action 2 for 'Hello streaming agent!'."
        actual_details_event2 = received_events_data[2].data["details"]
        assert actual_details_event2 == expected_detail_string_event2
        
        assert received_events_data[3].type == "output"
        expected_content_event3 = f"Agent output chunk 3 for 'Hello streaming agent!'."
        actual_content_event3 = received_events_data[3].data["content"]
        assert actual_content_event3 == expected_content_event3

        assert received_events_data[4].type == "status"
        assert received_events_data[4].data["message"] == "Agent task completed."
        assert received_events_data[4].data["final"] is True
        
        mock_stream_method.assert_called_once()
        called_with_request = mock_stream_method.call_args[0][0]
        assert isinstance(called_with_request, RunAgentRequest)
        assert called_with_request.agent_id == agent_id
        assert called_with_request.input_prompt == "Hello streaming agent!"

    await test_agent_config_handler.delete_global_agent_config(agent_id)
