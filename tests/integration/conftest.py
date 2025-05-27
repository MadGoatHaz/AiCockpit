# tests/integration/conftest.py
import pytest
from pathlib import Path
import os 
import sys 
from typing import AsyncGenerator, Optional 
import httpx 
from unittest import mock 

from acp_backend.config import Settings 
from acp_backend.core.session_handler import SessionHandler
from acp_backend.core.agent_config_handler import AgentConfigHandler
from acp_backend.core.fs_manager import FileSystemManager
from acp_backend.core.llm_manager import LLMManager
from acp_backend.core.agent_executor import AgentExecutor
from acp_backend.main import app 

from acp_backend.dependencies import (
    get_session_handler_dependency,
    get_llm_manager_dependency,
    get_agent_config_handler_dependency,
    get_fs_manager_dependency,
    get_agent_executor_dependency,
    get_settings_dependency as get_app_settings_dependency 
)
from acp_backend.models.llm_models import LLMModelInfo 


@pytest.fixture(scope="function")
def temp_settings_for_test(tmp_path: Path, monkeypatch) -> Settings:
    global_agent_configs_dir_name = Settings.model_fields['GLOBAL_AGENT_CONFIGS_DIR_NAME'].default
    temp_work_sessions_dir = tmp_path / "work_sessions"
    temp_logs_dir = tmp_path / "logs"
    temp_temp_dir = tmp_path / "temp"
    temp_models_dir = tmp_path / "llm_models"

    settings_for_test = Settings(
        WORK_SESSIONS_DIR=temp_work_sessions_dir,
        LOG_DIR=temp_logs_dir,
        TEMP_DIR=temp_temp_dir,
        MODELS_DIR=temp_models_dir
    )
    
    settings_for_test.WORK_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    settings_for_test.LOG_DIR.mkdir(parents=True, exist_ok=True)
    settings_for_test.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    settings_for_test.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    settings_for_test.get_global_agent_configs_path().mkdir(parents=True, exist_ok=True)

    from acp_backend import config as app_config_module 
    original_settings_in_module = app_config_module.settings
    monkeypatch.setattr(app_config_module, "settings", settings_for_test)
    
    # Minimal debug print for settings
    # print(f"DEBUG_CONFTEST_SETTINGS: temp_settings_for_test.WORK_SESSIONS_DIR set to: {settings_for_test.WORK_SESSIONS_DIR}", file=sys.stderr)

    yield settings_for_test

    monkeypatch.setattr(app_config_module, "settings", original_settings_in_module)


@pytest.fixture(scope="function")
def test_session_handler(temp_settings_for_test: Settings) -> SessionHandler:
    handler = SessionHandler(settings_override=temp_settings_for_test) 
    assert handler.sessions_base_dir == temp_settings_for_test.WORK_SESSIONS_DIR
    return handler

@pytest.fixture(scope="function")
def test_agent_config_handler(temp_settings_for_test: Settings, test_session_handler: SessionHandler) -> AgentConfigHandler:
    handler = AgentConfigHandler(
        session_handler_instance=test_session_handler, 
        settings_override=temp_settings_for_test
    )
    assert handler.global_configs_base_path == temp_settings_for_test.get_global_agent_configs_path()
    return handler

@pytest.fixture(scope="function")
def test_llm_manager(temp_settings_for_test: Settings, monkeypatch) -> Optional[LLMManager]:
    mock_llm_manager = mock.Mock(spec=LLMManager)
    async def mock_get_model_details(model_id: str) -> Optional[LLMModelInfo]:
        # print(f"DEBUG_CONFTEST_MOCK_LLM: Mocking get_model_details for {model_id}", file=sys.stderr) # Can be kept if needed
        return LLMModelInfo(
            id=model_id, name=f"Mocked {model_id}", path=f"/mock/path/{model_id}.gguf", 
            size_gb=0.01, quantization="Q0_0", loaded=True, backend="mock"
        )
    mock_llm_manager.get_model_details.side_effect = mock_get_model_details
    mock_llm_manager.get_loaded_models = mock.AsyncMock(return_value=[])
    mock_llm_manager.discover_models = mock.AsyncMock(return_value=[])
    mock_llm_manager.load_model = mock.AsyncMock(return_value=LLMModelInfo(id="mock-llm", name="Mock LLM", loaded=True, backend="mock"))
    mock_llm_manager.unload_model = mock.AsyncMock(return_value=LLMModelInfo(id="mock-llm", name="Mock LLM", loaded=False, backend="mock"))
    mock_llm_manager.release = mock.Mock() 
    return mock_llm_manager 

@pytest.fixture(scope="function")
def test_fs_manager(test_session_handler: SessionHandler, temp_settings_for_test: Settings) -> FileSystemManager:
    handler = FileSystemManager(session_handler_instance=test_session_handler)
    return handler

@pytest.fixture(scope="function", autouse=True)
async def test_client(
    temp_settings_for_test: Settings, 
    test_session_handler: SessionHandler, 
    test_agent_config_handler: AgentConfigHandler, 
    test_fs_manager: FileSystemManager,
    test_llm_manager: Optional[LLMManager]
) -> AsyncGenerator[httpx.AsyncClient, None]:
    
    def override_settings_dependency(): 
        return temp_settings_for_test
    
    def override_session_handler(): 
        return test_session_handler
        
    def override_agent_config_handler(): 
        return test_agent_config_handler
        
    def override_fs_manager(): 
        return test_fs_manager
        
    def override_llm_manager(): 
        return test_llm_manager
        
    def override_agent_executor(): 
        instance = AgentExecutor(
            agent_config_handler_instance=test_agent_config_handler, 
            llm_manager_instance=test_llm_manager 
        )
        return instance
    
    original_overrides = app.dependency_overrides.copy()

    app.dependency_overrides[get_app_settings_dependency] = override_settings_dependency
    app.dependency_overrides[get_session_handler_dependency] = override_session_handler
    app.dependency_overrides[get_agent_config_handler_dependency] = override_agent_config_handler
    app.dependency_overrides[get_fs_manager_dependency] = override_fs_manager
    app.dependency_overrides[get_llm_manager_dependency] = override_llm_manager
    app.dependency_overrides[get_agent_executor_dependency] = override_agent_executor
    
    print(f"INFO: Pytest conftest.py - All dependency overrides applied for test client.", file=sys.stderr) # Kept this one
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        yield client
    
    app.dependency_overrides = original_overrides
    # print(f"DEBUG_CONFTEST_CLIENT_TEARDOWN: Overrides restored.", file=sys.stderr) # Can be removed
