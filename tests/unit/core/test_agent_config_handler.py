# tests/unit/core/test_agent_config_handler.py
import pytest
import json
import os 
import uuid
import datetime
import asyncio 
from pathlib import Path 
import sys 
from unittest import mock 
from unittest.mock import AsyncMock 
import shutil # ADDED IMPORT

from acp_backend.models.agent_models import AgentConfig
from acp_backend.models.work_session_models import WorkSession
from acp_backend.core.agent_config_handler import AgentConfigHandler
from acp_backend.core.session_handler import LOCAL_AGENTS_DIR_NAME, SESSION_DATA_DIRNAME 
from acp_backend.config import Settings 
from acp_backend.core.session_handler import SessionHandler as SessionHandlerClass 


mocked_session_handler_for_ach_tests = mock.Mock(spec=SessionHandlerClass)
mocked_session_handler_for_ach_tests.get_session = AsyncMock()
mocked_session_handler_for_ach_tests._get_session_folder_path = mock.Mock() 
mocked_session_handler_for_ach_tests._validate_session_id_format = mock.Mock()
mocked_session_handler_for_ach_tests._get_session_data_path = mock.Mock() 


@pytest.fixture(autouse=True)
def reset_global_mocked_session_handler(): 
    mocked_session_handler_for_ach_tests.get_session.reset_mock()
    mocked_session_handler_for_ach_tests._get_session_folder_path.reset_mock()
    mocked_session_handler_for_ach_tests._validate_session_id_format.reset_mock()
    mocked_session_handler_for_ach_tests._get_session_data_path.reset_mock()
    mocked_session_handler_for_ach_tests.get_session.side_effect = None
    mocked_session_handler_for_ach_tests._get_session_folder_path.side_effect = None
    mocked_session_handler_for_ach_tests._validate_session_id_format.side_effect = None
    mocked_session_handler_for_ach_tests._get_session_data_path.side_effect = None


@pytest.fixture
def handler(tmp_path: Path) -> AgentConfigHandler:
    # Create a distinct Settings instance for these unit tests to avoid conflicts
    # with global patching done in integration tests.
    ach_unit_test_settings = Settings(
        WORK_SESSIONS_DIR=tmp_path / "ach_unit_test_work_sessions",
        # GLOBAL_AGENT_CONFIGS_DIR_NAME is taken from the default in Settings model
    )
    # Ensure the paths for this specific settings instance exist
    ach_unit_test_settings.WORK_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    ach_unit_test_settings.get_global_agent_configs_path().mkdir(parents=True, exist_ok=True)
    
    test_handler = AgentConfigHandler(
        session_handler_instance=mocked_session_handler_for_ach_tests,
        settings_override=ach_unit_test_settings 
    )
    assert test_handler.global_configs_base_path == ach_unit_test_settings.get_global_agent_configs_path()
    yield test_handler

@pytest.mark.asyncio
async def test_save_and_get_global_agent_config(handler: AgentConfigHandler, tmp_path: Path):
    agent_id = str(uuid.uuid4())
    config_data = AgentConfig(agent_id=agent_id, name="Test Agent", agent_type="CodeAgent", llm_model_id="test-llm-v1")
    await handler.save_global_agent_config(config_data)
    expected_file = handler.global_configs_base_path / f"{agent_id}.json"
    assert await asyncio.to_thread(expected_file.exists)
    retrieved_config = await handler.get_global_agent_config(agent_id)
    assert retrieved_config is not None
    assert retrieved_config.agent_id == agent_id
    # For a new config, created_at and updated_at should be identical
    assert retrieved_config.created_at == retrieved_config.updated_at

@pytest.mark.asyncio
async def test_get_non_existent_global_config(handler: AgentConfigHandler):
    assert await handler.get_global_agent_config(str(uuid.uuid4())) is None

@pytest.mark.asyncio
async def test_save_updates_timestamps(handler: AgentConfigHandler, tmp_path: Path):
    agent_id = str(uuid.uuid4())
    config1 = AgentConfig(agent_id=agent_id, name="Agent v1", agent_type="CodeAgent", llm_model_id="llm1")
    await handler.save_global_agent_config(config1)
    retrieved1 = await handler.get_global_agent_config(agent_id)
    assert retrieved1 is not None
    
    # Ensure enough time passes for updated_at to be different
    await asyncio.sleep(0.01) 
    
    # When updating, created_at should be preserved, updated_at should change.
    # The AgentConfig model passed to save_global_agent_config should not have created_at set by the test,
    # the handler logic should preserve it from the existing_config.
    update_payload = AgentConfig(
        agent_id=agent_id, 
        name="Agent v2", # Changed name
        agent_type="CodeAgent", 
        llm_model_id="llm1" 
        # created_at is NOT set here, should be preserved by handler
        # updated_at will be set by handler
    )
    await handler.save_global_agent_config(update_payload)
    retrieved2 = await handler.get_global_agent_config(agent_id)
    
    assert retrieved2 is not None
    assert retrieved2.created_at == retrieved1.created_at # Must be preserved
    assert retrieved2.updated_at > retrieved1.updated_at # Must be newer
    assert retrieved2.name == "Agent v2"


@pytest.mark.asyncio
async def test_list_global_agent_configs(handler: AgentConfigHandler, tmp_path: Path):
    for item in handler.global_configs_base_path.glob("*.json"): 
        await asyncio.to_thread(item.unlink)

    ids = [str(uuid.uuid4()) for _ in range(3)]
    await handler.save_global_agent_config(AgentConfig(agent_id=ids[0], name="Agent A", agent_type="CodeAgent", llm_model_id="llm1"))
    await asyncio.sleep(0.05) 
    await handler.save_global_agent_config(AgentConfig(agent_id=ids[2], name="Agent C", agent_type="CodeAgent", llm_model_id="llm1")) 
    await asyncio.sleep(0.05) 
    await handler.save_global_agent_config(AgentConfig(agent_id=ids[1], name="Agent B", agent_type="ToolAgent", llm_model_id="llm2")) 
    
    listed_configs = await handler.list_global_agent_configs()
    assert len(listed_configs) == 3
    assert listed_configs[0].name == "Agent B"
    assert listed_configs[1].name == "Agent C"
    assert listed_configs[2].name == "Agent A"


@pytest.mark.asyncio
async def test_delete_global_agent_config(handler: AgentConfigHandler, tmp_path: Path):
    agent_id = str(uuid.uuid4())
    config_data = AgentConfig(agent_id=agent_id, name="To Delete", agent_type="CodeAgent", llm_model_id="llm-del")
    await handler.save_global_agent_config(config_data)
    assert await asyncio.to_thread((handler.global_configs_base_path / f"{agent_id}.json").exists)
    assert await handler.delete_global_agent_config(agent_id) is True
    assert not await asyncio.to_thread((handler.global_configs_base_path / f"{agent_id}.json").exists)
    assert await handler.get_global_agent_config(agent_id) is None


def mock_session_paths_for_ach_tests(session_id: str, tmp_path: Path, session_exists: bool = True):
    session_base_path_for_test = tmp_path / "sessions_root_for_ach" 
    session_folder = session_base_path_for_test / session_id
    
    mocked_session_handler_for_ach_tests._get_session_folder_path.return_value = session_folder
    mocked_session_handler_for_ach_tests._get_session_data_path.return_value = session_folder / SESSION_DATA_DIRNAME
    if session_exists:
        mocked_session_handler_for_ach_tests.get_session.return_value = WorkSession(
            session_id=session_id, name="Test Session", 
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            last_accessed=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        session_folder.mkdir(parents=True, exist_ok=True)
        (session_folder / LOCAL_AGENTS_DIR_NAME).mkdir(parents=True, exist_ok=True)
    else:
        mocked_session_handler_for_ach_tests.get_session.return_value = None
    mocked_session_handler_for_ach_tests._validate_session_id_format.return_value = None


@pytest.mark.asyncio
async def test_save_and_get_local_agent_config(handler: AgentConfigHandler, tmp_path: Path):
    session_id = "test_session_1_ach"
    agent_id = str(uuid.uuid4())
    mock_session_paths_for_ach_tests(session_id, tmp_path, session_exists=True)

    config_data = AgentConfig(agent_id=agent_id, name="Local Agent", agent_type="CodeAgent", llm_model_id="local-llm")
    await handler.save_local_agent_config(session_id, config_data)

    expected_local_agents_dir = tmp_path / "sessions_root_for_ach" / session_id / LOCAL_AGENTS_DIR_NAME
    expected_file = expected_local_agents_dir / f"{agent_id}.json"
    assert await asyncio.to_thread(expected_file.exists)

    retrieved_config = await handler.get_local_agent_config(session_id, agent_id)
    assert retrieved_config is not None
    assert retrieved_config.agent_id == agent_id
    assert retrieved_config.created_at == retrieved_config.updated_at

@pytest.mark.asyncio
async def test_get_local_agent_config_session_not_found_returns_none(handler: AgentConfigHandler, tmp_path: Path):
    session_id = "non_existent_session_ach"
    agent_id = str(uuid.uuid4())
    mock_session_paths_for_ach_tests(session_id, tmp_path, session_exists=False)
    result = await handler.get_local_agent_config(session_id, agent_id)
    assert result is None

@pytest.mark.asyncio
async def test_save_local_agent_config_session_not_found(handler: AgentConfigHandler):
    session_id = "non_existent_session_for_save_ach"
    agent_id = str(uuid.uuid4())
    mocked_session_handler_for_ach_tests.get_session.return_value = None 
    config_data = AgentConfig(agent_id=agent_id, name="Local Agent", agent_type="CodeAgent", llm_model_id="local-llm")
    with pytest.raises(FileNotFoundError, match=f"Work Session ID '{session_id}' not found"):
        await handler.save_local_agent_config(session_id, config_data)

@pytest.mark.asyncio
async def test_list_local_agent_configs(handler: AgentConfigHandler, tmp_path: Path):
    session_id = "session_for_listing_ach"
    mock_session_paths_for_ach_tests(session_id, tmp_path, session_exists=True)
    
    local_agents_dir = tmp_path / "sessions_root_for_ach" / session_id / LOCAL_AGENTS_DIR_NAME
    if await asyncio.to_thread(local_agents_dir.exists):
        for item in await asyncio.to_thread(list, local_agents_dir.glob("*.json")): 
            await asyncio.to_thread(item.unlink)
    else:
        await asyncio.to_thread(local_agents_dir.mkdir, parents=True, exist_ok=True)

    ids = [str(uuid.uuid4()) for _ in range(2)]
    config1 = AgentConfig(agent_id=ids[0], name="Local1", agent_type="CodeAgent", llm_model_id="llm1")
    await handler.save_local_agent_config(session_id, config1)
    await asyncio.sleep(0.05) 
    config2 = AgentConfig(agent_id=ids[1], name="Local2", agent_type="ToolAgent", llm_model_id="llm2")
    await handler.save_local_agent_config(session_id, config2)

    listed_configs = await handler.list_local_agent_configs(session_id)
    assert len(listed_configs) == 2
    assert listed_configs[0].name == "Local2" 
    assert listed_configs[1].name == "Local1"

@pytest.mark.asyncio
async def test_list_local_configs_no_agents_dir(handler: AgentConfigHandler, tmp_path: Path):
    session_id = "session_no_agents_dir_ach"
    mock_session_paths_for_ach_tests(session_id, tmp_path, session_exists=True) 
    local_agents_dir = tmp_path / "sessions_root_for_ach" / session_id / LOCAL_AGENTS_DIR_NAME
    if await asyncio.to_thread(local_agents_dir.exists):
        await asyncio.to_thread(shutil.rmtree, local_agents_dir) # shutil was missing
    
    mocked_session_handler_for_ach_tests.get_session.return_value = WorkSession(session_id=session_id, name="s",created_at="n",last_accessed="n")
    
    listed_configs = await handler.list_local_agent_configs(session_id)
    assert listed_configs == []

@pytest.mark.asyncio
async def test_delete_local_agent_config(handler: AgentConfigHandler, tmp_path: Path):
    session_id = "session_for_delete_ach"
    agent_id = str(uuid.uuid4())
    mock_session_paths_for_ach_tests(session_id, tmp_path, session_exists=True)
    
    config_data = AgentConfig(agent_id=agent_id, name="LocalToDelete", agent_type="CodeAgent", llm_model_id="llm-del")
    await handler.save_local_agent_config(session_id, config_data)
    
    expected_file = tmp_path / "sessions_root_for_ach" / session_id / LOCAL_AGENTS_DIR_NAME / f"{agent_id}.json"
    assert await asyncio.to_thread(expected_file.exists)

    assert await handler.delete_local_agent_config(session_id, agent_id) is True
    assert not await asyncio.to_thread(expected_file.exists)
    assert await handler.get_local_agent_config(session_id, agent_id) is None

@pytest.mark.asyncio
async def test_get_effective_agent_config_global_only(handler: AgentConfigHandler, tmp_path: Path):
    global_agent_id = str(uuid.uuid4())
    global_config = AgentConfig(agent_id=global_agent_id, name="EffectiveGlobal", agent_type="CodeAgent", llm_model_id="g-llm")
    await handler.save_global_agent_config(global_config)
    
    mocked_session_handler_for_ach_tests.get_session.return_value = None 
    retrieved = await handler.get_effective_agent_config(global_agent_id)
    assert retrieved is not None; assert retrieved.name == "EffectiveGlobal"

    session_id = "session_for_effective_global_ach"
    mock_session_paths_for_ach_tests(session_id, tmp_path, session_exists=True)
    with mock.patch.object(handler, 'get_local_agent_config', AsyncMock(return_value=None)) as mock_get_local:
        retrieved_with_session = await handler.get_effective_agent_config(global_agent_id, session_id=session_id)
        mock_get_local.assert_called_once_with(session_id, global_agent_id)
    assert retrieved_with_session is not None
    assert retrieved_with_session.name == "EffectiveGlobal"

@pytest.mark.asyncio
async def test_get_effective_agent_config_local_overrides_global(handler: AgentConfigHandler, tmp_path: Path):
    agent_id = str(uuid.uuid4()) 
    session_id = "session_for_override_ach"
    mock_session_paths_for_ach_tests(session_id, tmp_path, session_exists=True)
    
    global_config = AgentConfig(agent_id=agent_id, name="GlobalOriginal", agent_type="CodeAgent", llm_model_id="g-llm")
    await handler.save_global_agent_config(global_config)
    
    local_config_obj = AgentConfig(agent_id=agent_id, name="LocalOverride", agent_type="ToolAgent", llm_model_id="l-llm")
    
    with mock.patch.object(handler, 'get_local_agent_config', AsyncMock(return_value=local_config_obj)) as mock_get_local:
        retrieved = await handler.get_effective_agent_config(agent_id, session_id=session_id)
        mock_get_local.assert_called_once_with(session_id, agent_id)
    assert retrieved is not None
    assert retrieved.name == "LocalOverride"

    with mock.patch.object(handler, 'get_local_agent_config', AsyncMock(return_value=None)) as mock_get_local_none:
        retrieved_global_again = await handler.get_effective_agent_config(agent_id) 
        mock_get_local_none.assert_not_called() 
    assert retrieved_global_again is not None
    assert retrieved_global_again.name == "GlobalOriginal"

@pytest.mark.asyncio
async def test_get_effective_agent_config_local_only(handler: AgentConfigHandler, tmp_path: Path):
    agent_id = str(uuid.uuid4())
    session_id = "session_for_local_only_ach"
    mock_session_paths_for_ach_tests(session_id, tmp_path, session_exists=True)
    
    local_config_obj = AgentConfig(agent_id=agent_id, name="OnlyLocal", agent_type="ToolAgent", llm_model_id="l-llm")
    
    with mock.patch.object(handler, 'get_local_agent_config', new_callable=AsyncMock) as mock_get_local, \
         mock.patch.object(handler, 'get_global_agent_config', new_callable=AsyncMock) as mock_get_global:
        mock_get_local.return_value = local_config_obj
        
        retrieved = await handler.get_effective_agent_config(agent_id, session_id=session_id)
        mock_get_local.assert_called_once_with(session_id, agent_id)
        mock_get_global.assert_not_called() 
        assert retrieved is not None
        assert retrieved.name == "OnlyLocal"
        
        mock_get_local.reset_mock(); mock_get_local.return_value = None 
        mock_get_global.reset_mock(); mock_get_global.return_value = None 
        retrieved_global = await handler.get_effective_agent_config(agent_id) 
        mock_get_local.assert_not_called() 
        mock_get_global.assert_called_once_with(agent_id)
        assert retrieved_global is None


@pytest.mark.asyncio
async def test_list_empty_global_configs(handler: AgentConfigHandler, tmp_path: Path): 
    for item in handler.global_configs_base_path.glob("*.json"): 
        await asyncio.to_thread(item.unlink)
    assert await handler.list_global_agent_configs() == []

@pytest.mark.asyncio
async def test_delete_non_existent_global_config(handler: AgentConfigHandler): 
    assert await handler.delete_global_agent_config(str(uuid.uuid4())) is True

@pytest.mark.asyncio
async def test_invalid_agent_id_operations(handler: AgentConfigHandler): 
    invalid_ids = ["../escape", "path/slash", "path\\slash", ""]
    for invalid_id in invalid_ids:
        with pytest.raises(ValueError, match="Invalid agent_id format"):
            await handler.save_global_agent_config(AgentConfig(agent_id=invalid_id, name="x", agent_type="y", llm_model_id="z"))
        with pytest.raises(ValueError, match="Invalid agent_id format"):
            await handler.get_global_agent_config(invalid_id)
        with pytest.raises(ValueError, match="Invalid agent_id format"):
            await handler.delete_global_agent_config(invalid_id)

@pytest.mark.asyncio
async def test_corrupted_json_file(handler: AgentConfigHandler, tmp_path: Path): 
    agent_id = str(uuid.uuid4())
    corrupted_file = handler._get_global_agent_config_file_path(agent_id) 
    await asyncio.to_thread(corrupted_file.parent.mkdir, parents=True, exist_ok=True)
    def _write_corrupted():
        with open(corrupted_file, "w", encoding="utf-8") as f: f.write("{'invalid_json': True,")
    await asyncio.to_thread(_write_corrupted)
    assert await handler.get_global_agent_config(agent_id) is None

@pytest.mark.asyncio
async def test_mismatched_agent_id_in_file(handler: AgentConfigHandler, tmp_path: Path): 
    agent_id_filename = str(uuid.uuid4()); agent_id_internal = str(uuid.uuid4()) 
    file_path = handler._get_global_agent_config_file_path(agent_id_filename)
    await asyncio.to_thread(file_path.parent.mkdir, parents=True, exist_ok=True)
    config_data_internal = AgentConfig(agent_id=agent_id_internal, name="Mismatched", agent_type="CodeAgent", llm_model_id="test")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    config_data_internal.created_at = now; config_data_internal.updated_at = now
    def _write_mismatched():
        with open(file_path, "w", encoding="utf-8") as f: json.dump(config_data_internal.model_dump(mode="json"), f, indent=4)
    await asyncio.to_thread(_write_mismatched)
    assert await handler.get_global_agent_config(agent_id_filename) is None
