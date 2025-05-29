# tests/integration/conftest.py
import pytest
from pathlib import Path
import os 
import sys 
from typing import AsyncGenerator, Optional, List
import httpx 
from unittest import mock 
import asyncio

from acp_backend.config import AppSettings, app_settings as original_app_settings_module_instance
from acp_backend.core.session_handler import SessionHandler
from acp_backend.core.agent_config_handler import AgentConfigHandler
from acp_backend.core.fs_manager import FileSystemManager
from acp_backend.core.llm_manager import LLMManager
from acp_backend.core.agent_executor import AgentExecutor
from acp_backend.main import app 

from acp_backend.dependencies import (
    get_session_handler,
    get_llm_manager,
    get_agent_config_handler,
    get_fs_manager,
    get_agent_executor,
    get_app_settings as get_app_settings_dependency,
    _session_handler_instance,
    _agent_config_handler_instance,
    _agent_executor_instance,
    _llm_manager_instance,
    _fs_manager_instance
)
from acp_backend.models.llm_models import LLMModelInfo, LLM, LLMConfig, LLMModelType, LLMStatus, LLMChatMessage, LLMChatCompletion

from fastapi import FastAPI
from httpx import AsyncClient


@pytest.fixture(scope="session")
def session_tmp_path_factory(tmp_path_factory):
    return tmp_path_factory.mktemp("session_global_resources")

@pytest.fixture(scope="session")
def temp_settings_for_test_session_scope(session_tmp_path_factory) -> AppSettings:
    test_specific_tmp_path = session_tmp_path_factory / "session_app_settings"
    test_specific_tmp_path.mkdir(parents=True, exist_ok=True)

    temp_work_sessions_dir = test_specific_tmp_path / "s_work_sessions"
    temp_global_agents_dir = test_specific_tmp_path / "s_global_agent_configs"
    temp_models_dir = test_specific_tmp_path / "s_models_dir"
    temp_logs_dir = test_specific_tmp_path / "s_logs"

    temp_work_sessions_dir.mkdir(parents=True, exist_ok=True)
    temp_global_agents_dir.mkdir(parents=True, exist_ok=True)
    temp_models_dir.mkdir(parents=True, exist_ok=True)
    temp_logs_dir.mkdir(parents=True, exist_ok=True)
    
    return AppSettings(
        ACP_BASE_DIR=test_specific_tmp_path,
        WORK_SESSIONS_DIR=temp_work_sessions_dir,
        GLOBAL_AGENT_CONFIGS_DIR_NAME="_agent_configs_session",
        MODELS_DIR=temp_models_dir,
        LOG_DIR=temp_logs_dir,
        LOG_LEVEL="DEBUG", 
        ENABLE_AGENT_MODULE=True,
        ENABLE_LLM_SERVICE_MODULE=True, 
    )

@pytest.fixture(scope="session")
def test_session_handler_session_scope(temp_settings_for_test_session_scope: AppSettings) -> SessionHandler:
    return SessionHandler(base_dir=temp_settings_for_test_session_scope.WORK_SESSIONS_DIR)

@pytest.fixture(scope="session")
def test_agent_config_handler_session_scope(
    test_session_handler_session_scope: SessionHandler, 
    temp_settings_for_test_session_scope: AppSettings
) -> AgentConfigHandler:
    return AgentConfigHandler(
        session_handler_instance=test_session_handler_session_scope, 
        settings_override=temp_settings_for_test_session_scope
    )

@pytest.fixture(scope="session")
def test_llm_manager_session_scope(temp_settings_for_test_session_scope: AppSettings) -> mock.Mock:
    mock_llm_manager = mock.Mock(spec=LLMManager)
    mock_llm_manager.get_llm_meta.return_value = mock.Mock(status="loaded") 
    mock_llm_manager.chat_completion = mock.AsyncMock(
        return_value=mock.Mock(choices=[mock.Mock(message=mock.Mock(content="Mocked LLM response"))])
    )
    async def mock_empty_stream(*args, **kwargs):
        if False:
            yield
    mock_llm_manager.stream_chat_completion = mock.AsyncMock(return_value=mock_empty_stream())

    return mock_llm_manager

@pytest.fixture(scope="session")
def app_for_integration_tests(
    temp_settings_for_test_session_scope: AppSettings,
    test_session_handler_session_scope: SessionHandler,
    test_agent_config_handler_session_scope: AgentConfigHandler,
    test_llm_manager_session_scope: mock.Mock
) -> FastAPI:
    app.dependency_overrides[get_app_settings_dependency] = lambda: temp_settings_for_test_session_scope
    app.dependency_overrides[get_session_handler] = lambda: test_session_handler_session_scope
    app.dependency_overrides[get_agent_config_handler] = lambda: test_agent_config_handler_session_scope
    app.dependency_overrides[get_llm_manager] = lambda: test_llm_manager_session_scope
    
    print("INFO: Pytest conftest.py - Session-scoped dependency overrides applied for FastAPI app.")
    return app

@pytest.fixture(scope="function")
def temp_settings_for_test(tmp_path_factory, temp_settings_for_test_session_scope: AppSettings) -> AppSettings:
    test_specific_tmp_path = tmp_path_factory.mktemp("test_func_resources")
    
    temp_work_sessions_dir = test_specific_tmp_path / "work_sessions"
    temp_global_agents_dir_name = "_agent_configs_func" 
    temp_models_dir = test_specific_tmp_path / "models_dir"
    temp_logs_dir = test_specific_tmp_path / "logs"

    temp_work_sessions_dir.mkdir(parents=True, exist_ok=True)
    (temp_work_sessions_dir / temp_global_agents_dir_name).mkdir(parents=True, exist_ok=True)
    temp_models_dir.mkdir(parents=True, exist_ok=True)
    temp_logs_dir.mkdir(parents=True, exist_ok=True)
    
    return temp_settings_for_test_session_scope.model_copy(update={
        "ACP_BASE_DIR": test_specific_tmp_path,
        "WORK_SESSIONS_DIR": temp_work_sessions_dir,
        "GLOBAL_AGENT_CONFIGS_DIR_NAME": temp_global_agents_dir_name,
        "MODELS_DIR": temp_models_dir,
        "LOG_DIR": temp_logs_dir,
        "LOG_LEVEL": "DEBUG",
    })

@pytest.fixture(scope="function")
def test_session_handler(temp_settings_for_test: AppSettings) -> SessionHandler:
    return SessionHandler(base_dir=temp_settings_for_test.WORK_SESSIONS_DIR)

@pytest.fixture(scope="function")
def test_agent_config_handler(
    test_session_handler: SessionHandler, 
    temp_settings_for_test: AppSettings
) -> AgentConfigHandler:
    return AgentConfigHandler(
        session_handler_instance=test_session_handler, 
        settings_override=temp_settings_for_test
    )

@pytest.fixture(scope="function")
def test_llm_manager(temp_settings_for_test: AppSettings) -> mock.Mock:
    mock_llm_manager = mock.Mock(spec=LLMManager)
    mock_llm_manager.get_llm_meta.return_value = mock.Mock(status="loaded")
    async def mock_llm_response_func(*args, **kwargs):
        return mock.Mock(choices=[mock.Mock(message=mock.Mock(content="Mocked LLM response"))])
    
    mock_llm_manager.chat_completion = mock.AsyncMock(side_effect=mock_llm_response_func)
    
    async def mock_streaming_response_func(*args, **kwargs):
        yield AgentOutputChunk(run_id="mock_run", type="output", data="Mocked LLM stream chunk 1")
        await asyncio.sleep(0.01)
        yield AgentOutputChunk(run_id="mock_run", type="output", data="Mocked LLM stream chunk 2")

    async def combined_chat_completion_mock(model_id, messages, stream=False, **kwargs):
        if stream:
            async def mock_stream():
                yield mock.Mock(choices=[mock.Mock(message=mock.Mock(content="Stream chunk 1 "))])
                await asyncio.sleep(0.01)
                yield mock.Mock(choices=[mock.Mock(message=mock.Mock(content="Stream chunk 2"))])
            return mock_stream()
        else:
            return mock.Mock(choices=[mock.Mock(message=mock.Mock(content="Mocked LLM non-stream response"))])

    mock_llm_manager.chat_completion = mock.AsyncMock(side_effect=combined_chat_completion_mock)
    mock_llm_manager.stream_process_chat_completion = mock.AsyncMock(return_value=mock_streaming_response_func())

    return mock_llm_manager

@pytest.fixture(scope="function")
def test_fs_manager(test_session_handler: SessionHandler, temp_settings_for_test: AppSettings) -> FileSystemManager:
    handler = FileSystemManager(session_handler_instance=test_session_handler)
    return handler

@pytest.fixture(scope="function", autouse=True)
async def test_client(
    app_for_integration_tests: FastAPI, 
    temp_settings_for_test: AppSettings,
    test_session_handler: SessionHandler,
    test_agent_config_handler: AgentConfigHandler,
    test_fs_manager: FileSystemManager,
    test_llm_manager: mock.Mock
) -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an HTTPX AsyncClient for making requests to the FastAPI app.
    Dependencies are overridden here on a per-function basis to ensure
    that function-scoped fixtures (like tmp_path based handlers) are used.
    """
    import acp_backend.dependencies as deps 
    
    deps._session_handler_instance = None
    deps._agent_config_handler_instance = None
    deps._llm_manager_instance = None
    deps._fs_manager_instance = None
    deps._agent_executor_instance = None

    original_overrides = app_for_integration_tests.dependency_overrides.copy()

    app_for_integration_tests.dependency_overrides[get_app_settings_dependency] = lambda: temp_settings_for_test
    app_for_integration_tests.dependency_overrides[get_session_handler] = lambda: test_session_handler
    app_for_integration_tests.dependency_overrides[get_agent_config_handler] = lambda: test_agent_config_handler
    app_for_integration_tests.dependency_overrides[get_fs_manager] = lambda: test_fs_manager
    app_for_integration_tests.dependency_overrides[get_llm_manager] = lambda: test_llm_manager
    
    print("INFO: Pytest conftest.py - Function-scoped dependency overrides applied for test client.")
    
    async with AsyncClient(transport=httpx.ASGITransport(app=app_for_integration_tests), base_url="http://testserver") as client:
        yield client
    
    app_for_integration_tests.dependency_overrides = original_overrides
    
    deps._session_handler_instance = None
    deps._agent_config_handler_instance = None
    deps._llm_manager_instance = None
    deps._fs_manager_instance = None
    deps._agent_executor_instance = None

    print("INFO: Pytest conftest.py - Dependency overrides cleared after test client.")
