# tests/integration/test_agent_execution_scoping.py
import pytest
import uuid
import sys 
from typing import Dict, Any, Optional, AsyncGenerator
import asyncio # ADDED IMPORT

import httpx
from fastapi import FastAPI, status

from acp_backend.main import app 
from acp_backend.models.agent_models import AgentConfig
from acp_backend.models.work_session_models import WorkSession, CreateWorkSessionRequest
from acp_backend.models.work_board_models import FileNode 

# No direct imports of handler instances here, they come via Depends in test_client fixture

pytestmark = pytest.mark.asyncio
BASE_URL = "http://testserver" 

# Helper functions now directly use the injected handler instances from the fixture
async def _create_global_agent_for_test_helper(agent_data: Dict[str, Any], agent_config_handler_instance) -> AgentConfig:
    config = AgentConfig(**agent_data)
    await agent_config_handler_instance.save_global_agent_config(config)
    return config

async def _create_local_agent_for_test_helper(session_id: str, agent_data: Dict[str, Any], agent_config_handler_instance) -> AgentConfig:
    config = AgentConfig(**agent_data)
    await agent_config_handler_instance.save_local_agent_config(session_id, config)
    return config

async def _create_session_for_test_helper(session_name: str, session_handler_instance) -> WorkSession:
    req = CreateWorkSessionRequest(name=session_name)
    
    print(f"\nDEBUG_TEST: In _create_session_for_test_helper for session: {session_name}", file=sys.stderr)
    print(f"DEBUG_TEST: Type of 'session_handler_instance': {type(session_handler_instance)}", file=sys.stderr)
    
    s = await session_handler_instance.create_session(req) 
    return s

@pytest.fixture(autouse=True)
async def cleanup_created_entities_fixture(test_session_handler, test_agent_config_handler): # Inject handlers
    created_global_agent_ids = []
    created_local_agents = [] 
    created_session_ids = []

    async def _create_global_agent(agent_data: Dict[str, Any]) -> AgentConfig:
        config = await _create_global_agent_for_test_helper(agent_data, test_agent_config_handler)
        created_global_agent_ids.append(config.agent_id)
        return config

    async def _create_local_agent(session_id: str, agent_data: Dict[str, Any]) -> AgentConfig:
        config = await _create_local_agent_for_test_helper(session_id, agent_data, test_agent_config_handler)
        created_local_agents.append((session_id, config.agent_id))
        return config
    
    async def _create_session(session_name: str) -> WorkSession:
        s = await _create_session_for_test_helper(session_name, test_session_handler)
        created_session_ids.append(s.session_id)
        return s

    yield { 
        "create_global_agent": _create_global_agent,
        "create_local_agent": _create_local_agent,
        "create_session": _create_session
    }

    for agent_id in created_global_agent_ids:
        await test_agent_config_handler.delete_global_agent_config(agent_id)
    for session_id_val, agent_id_val in created_local_agents: 
        await test_agent_config_handler.delete_local_agent_config(session_id_val, agent_id_val)
    for session_id_val in created_session_ids: 
        await test_session_handler.delete_session(session_id_val)


async def test_run_agent_uses_global_config_when_no_session_id(test_client: httpx.AsyncClient, cleanup_created_entities_fixture):
    create_g_agent = cleanup_created_entities_fixture["create_global_agent"]
    agent_id = f"test-global-agent-{uuid.uuid4()}"
    await create_g_agent({
        "agent_id": agent_id, "name": "My Global Agent", 
        "agent_type": "GlobalTestAgent", "llm_model_id": "mock-llm"
    })

    run_request_data = {"agent_id": agent_id, "input_prompt": "Hello Global"}
    response = await test_client.post("/api/agents/run", json=run_request_data)
    
    assert response.status_code == status.HTTP_200_OK, response.text
    response_data = response.json()
    assert response_data["agent_id"] == agent_id
    assert f"Agent '{agent_id}' (session: None) processed input: 'Hello Global' (Placeholder Output)" in response_data["output"]


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
    await create_l_agent(session.session_id, {
        "agent_id": agent_id, "name": "My Local Agent",
        "agent_type": "LocalType", "llm_model_id": "mock-llm-local"
    })

    run_request_data = {"agent_id": agent_id, "input_prompt": "Hello Local", "session_id": session.session_id}
    response = await test_client.post("/api/agents/run", json=run_request_data)
    
    assert response.status_code == status.HTTP_200_OK, response.text
    response_data = response.json()
    assert response_data["agent_id"] == agent_id
    assert f"Agent '{agent_id}' (session: {session.session_id}) processed input: 'Hello Local' (Placeholder Output)" in response_data["output"]


async def test_run_agent_uses_global_config_if_local_not_found_in_session(test_client: httpx.AsyncClient, cleanup_created_entities_fixture):
    create_g_agent = cleanup_created_entities_fixture["create_global_agent"]
    create_sess = cleanup_created_entities_fixture["create_session"]

    session = await create_sess("session-for-global-fallback")
    agent_id = f"test-global-fallback-agent-{uuid.uuid4()}"

    await create_g_agent({
        "agent_id": agent_id, "name": "My Global Fallback Agent",
        "agent_type": "GlobalFallbackType", "llm_model_id": "mock-llm-global"
    })

    run_request_data = {"agent_id": agent_id, "input_prompt": "Hello Global Fallback", "session_id": session.session_id}
    response = await test_client.post("/api/agents/run", json=run_request_data)
    
    assert response.status_code == status.HTTP_200_OK, response.text
    response_data = response.json()
    assert response_data["agent_id"] == agent_id
    assert f"Agent '{agent_id}' (session: {session.session_id}) processed input: 'Hello Global Fallback' (Placeholder Output)" in response_data["output"]


async def test_run_agent_404_if_no_config_found(test_client: httpx.AsyncClient, cleanup_created_entities_fixture):
    create_sess = cleanup_created_entities_fixture["create_session"]
    agent_id = f"non-existent-agent-{uuid.uuid4()}"
    run_request_data = {"agent_id": agent_id, "input_prompt": "Hello Nowhere"}
    
    response = await test_client.post("/api/agents/run", json=run_request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    session = await create_sess("session-for-404-test")
    run_request_with_session_data = {"agent_id": agent_id, "input_prompt": "Hello Nowhere in session", "session_id": session.session_id}
    response_with_session = await test_client.post("/api/agents/run", json=run_request_with_session_data)
    assert response_with_session.status_code == status.HTTP_404_NOT_FOUND
