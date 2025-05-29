# tests/integration/test_agent_execution_scoping.py
import pytest
import uuid
import sys 
from typing import Dict, Any, Optional, AsyncGenerator
import asyncio # ADDED IMPORT
import logging # ADDED IMPORT

import httpx
from fastapi import FastAPI, status

from acp_backend.main import app 
from acp_backend.models.agent_models import AgentConfig
from acp_backend.models.work_session_models import SessionMetadata, SessionCreate
from acp_backend.models.work_board_models import FileNode 
from acp_backend.core.session_handler import SessionHandler as ActualSessionHandlerClass
from acp_backend.core.agent_config_handler import AgentConfigHandler as ActualAgentConfigHandlerClass
from acp_backend.dependencies import get_session_handler, get_agent_config_handler

# No direct imports of handler instances here, they come via Depends in test_client fixture

# Set log level for the specific module to DEBUG for these tests
logging.getLogger("acp_backend.core.agent_config_handler").setLevel(logging.DEBUG)

pytestmark = pytest.mark.asyncio
BASE_URL = "http://testserver" 

# Keep track of created entities for cleanup
created_global_agent_ids: list[str] = []
created_local_agent_ids: dict[uuid.UUID, list[str]] = {}
created_session_ids: list[uuid.UUID] = []

# Helper functions now directly use the injected handler instances from the fixture
async def _create_global_agent_for_test_helper(agent_data: Dict[str, Any], agent_config_handler_instance: ActualAgentConfigHandlerClass) -> AgentConfig:
    config = AgentConfig(**agent_data)
    await agent_config_handler_instance.save_global_agent_config(config)
    return config

async def _create_local_agent_for_test_helper(session_id_str: str, agent_data: Dict[str, Any], agent_config_handler_instance: ActualAgentConfigHandlerClass) -> AgentConfig:
    config = AgentConfig(**agent_data)
    await agent_config_handler_instance.save_local_agent_config(session_id_str, config)
    return config

async def _create_session_for_test_helper(name_prefix: str) -> SessionMetadata:
    session_handler_instance: ActualSessionHandlerClass = app.dependency_overrides[get_session_handler]() # type: ignore
    print(f"DEBUG_TEST: In _create_session_for_test_helper for session: {name_prefix}", file=sys.stderr)
    print(f"DEBUG_TEST: Type of 'session_handler_instance': {type(session_handler_instance)}", file=sys.stderr)
    s = await session_handler_instance.create_session(SessionCreate(name=name_prefix))
    assert s is not None
    return s

@pytest.fixture(autouse=True)
async def cleanup_created_entities_fixture(test_session_handler: ActualSessionHandlerClass, test_agent_config_handler: ActualAgentConfigHandlerClass):
    # Clear lists at the beginning of each test that uses this fixture
    global created_global_agent_ids, created_local_agent_ids, created_session_ids
    created_global_agent_ids = []
    created_local_agent_ids = {}
    created_session_ids = []

    async def _create_global_agent(agent_data: Dict[str, Any]) -> AgentConfig:
        config = await _create_global_agent_for_test_helper(agent_data, test_agent_config_handler)
        created_global_agent_ids.append(config.agent_id)
        return config

    async def _create_local_agent(session_id_str: str, agent_data: Dict[str, Any]) -> AgentConfig:
        config = await _create_local_agent_for_test_helper(session_id_str, agent_data, test_agent_config_handler)
        created_local_agent_ids[uuid.UUID(session_id_str)] = [config.agent_id]
        return config
    
    async def _create_session(session_name: str) -> SessionMetadata:
        s = await _create_session_for_test_helper(session_name)
        created_session_ids.append(s.id)
        return s

    yield { 
        "create_global_agent": _create_global_agent,
        "create_local_agent": _create_local_agent,
        "create_session": _create_session
    }

    # Teardown: Clean up created entities
    # Use the directly injected handlers from fixture parameters for teardown
    agent_config_handler_for_cleanup: ActualAgentConfigHandlerClass = test_agent_config_handler
    session_handler_for_cleanup: ActualSessionHandlerClass = test_session_handler
    
    # Teardown local agents first
    # This requires created_local_agent_ids to be populated correctly by tests if they create local agents
    # For now, assuming direct calls to delete if IDs are known. The fixture itself doesn't track local agents yet.

    for sid_uuid in list(created_session_ids): # Iterate over a copy
        # Example of how local agent cleanup might be structured if tracked by session UUID
        if sid_uuid in created_local_agent_ids:
            for agent_id_str in created_local_agent_ids[sid_uuid]:
                try:
                    await agent_config_handler_for_cleanup.delete_local_agent_config(str(sid_uuid), agent_id_str)
                except Exception as e:
                    print(f"Error deleting local agent {agent_id_str} from session {sid_uuid} during teardown: {e}", file=sys.stderr)
            del created_local_agent_ids[sid_uuid]
        try:
            await session_handler_for_cleanup.delete_session(sid_uuid)
            created_session_ids.remove(sid_uuid)
        except Exception as e:
            print(f"Error deleting session {sid_uuid} during teardown: {e}", file=sys.stderr)

    for agent_id_str in list(created_global_agent_ids):
        try:
            await agent_config_handler_for_cleanup.delete_global_agent_config(agent_id_str)
            created_global_agent_ids.remove(agent_id_str)
        except Exception as e:
            print(f"Error deleting global agent {agent_id_str} during teardown: {e}", file=sys.stderr)


async def test_run_agent_uses_global_config_when_no_session_id(test_client: httpx.AsyncClient, cleanup_created_entities_fixture):
    create_g_agent = cleanup_created_entities_fixture["create_global_agent"]
    agent_id = f"test-global-agent-{uuid.uuid4()}"
    await create_g_agent({
        "agent_id": agent_id, "name": "My Global Agent", 
        "agent_type": "GlobalTestAgent", "llm_model_id": "mock-llm"
    })

    run_request_data = {"agent_id": agent_id, "input_prompt": "Hello Global"}
    response = await test_client.post("/agents/run", json=run_request_data)
    
    assert response.status_code == status.HTTP_200_OK, response.text
    response_data = response.json()
    assert response_data["agent_id"] == agent_id
    assert "Mocked LLM non-stream response" in response_data["output"]


async def test_run_agent_uses_local_config_when_session_id_provided(test_client: httpx.AsyncClient, cleanup_created_entities_fixture):
    create_g_agent = cleanup_created_entities_fixture["create_global_agent"]
    create_l_agent = cleanup_created_entities_fixture["create_local_agent"]
    create_sess = cleanup_created_entities_fixture["create_session"]

    session = await create_sess("session-with-local-agent")
    agent_id = f"test-local-override-agent-{uuid.uuid4()}"

    await create_g_agent({
        "agent_id": agent_id, "name": "My Global Agent (to be overridden)",
        "agent_type": "GlobalType", "llm_model_id": "mock-llm-global"
    })
    await create_l_agent(str(session.id), {
        "agent_id": agent_id, "name": "My Local Agent",
        "agent_type": "LocalType", "llm_model_id": "mock-llm-local"
    })

    run_request_data = {"agent_id": agent_id, "input_prompt": "Hello Local", "session_id": str(session.id)}
    response = await test_client.post("/agents/run", json=run_request_data)
    
    assert response.status_code == status.HTTP_200_OK, response.text
    response_data = response.json()
    assert response_data["agent_id"] == agent_id
    assert "Mocked LLM non-stream response" in response_data["output"]


async def test_run_agent_uses_global_config_if_local_not_found_in_session(test_client: httpx.AsyncClient, cleanup_created_entities_fixture):
    create_g_agent = cleanup_created_entities_fixture["create_global_agent"]
    create_sess = cleanup_created_entities_fixture["create_session"]

    session = await create_sess("session-for-global-fallback")
    agent_id = f"test-global-fallback-agent-{uuid.uuid4()}"

    await create_g_agent({
        "agent_id": agent_id, "name": "My Global Fallback Agent",
        "agent_type": "GlobalFallbackType", "llm_model_id": "mock-llm-global"
    })

    run_request_data = {"agent_id": agent_id, "input_prompt": "Hello Global Fallback", "session_id": str(session.id)}
    response = await test_client.post("/agents/run", json=run_request_data)
    
    assert response.status_code == status.HTTP_200_OK, response.text
    response_data = response.json()
    assert response_data["agent_id"] == agent_id
    assert "Mocked LLM non-stream response" in response_data["output"]


async def test_run_agent_404_if_no_config_found(test_client: httpx.AsyncClient, cleanup_created_entities_fixture):
    create_sess = cleanup_created_entities_fixture["create_session"]
    agent_id = f"non-existent-agent-{uuid.uuid4()}"
    run_request_data = {"agent_id": agent_id, "input_prompt": "Hello Nowhere"}
    
    response = await test_client.post("/agents/run", json=run_request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    session = await create_sess("session-for-404-test")
    run_request_with_session_data = {"agent_id": agent_id, "input_prompt": "Hello Nowhere in session", "session_id": str(session.id)}
    response_with_session = await test_client.post("/agents/run", json=run_request_with_session_data)
    assert response_with_session.status_code == status.HTTP_404_NOT_FOUND
