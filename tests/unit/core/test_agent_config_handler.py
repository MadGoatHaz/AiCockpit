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
from acp_backend.models.work_session_models import SessionMetadata
from acp_backend.core.agent_config_handler import AgentConfigHandler
from acp_backend.core.session_handler import SESSION_AGENTS_DIRNAME, SESSION_DATA_DIRNAME 
from acp_backend.config import AppSettings
from acp_backend.core.session_handler import SessionHandler as SessionHandlerClass 


# mocked_session_handler_for_ach_tests = mock.Mock(spec=SessionHandlerClass)
# mocked_session_handler_for_ach_tests.get_session = AsyncMock() # Old name
mocked_session_handler_for_ach_tests = AsyncMock(spec=SessionHandlerClass) # Make the whole mock an AsyncMock
mocked_session_handler_for_ach_tests.get_session_metadata = AsyncMock() # Correct method name

# Remove these as they are attributes of the AsyncMock now, or can be configured per test if needed
# mocked_session_handler_for_ach_tests._get_session_folder_path = mock.Mock() 
# mocked_session_handler_for_ach_tests._validate_session_id_format = mock.Mock()
# mocked_session_handler_for_ach_tests._get_session_data_path = mock.Mock() 

@pytest.fixture(autouse=True)
def reset_global_mocked_session_handler(): 
    mocked_session_handler_for_ach_tests.reset_mock() # Resets all attributes including those set with side_effect
    # Re-attach specific AsyncMocks for methods that need to be awaited or have side_effects controlled per test
    mocked_session_handler_for_ach_tests.get_session_metadata = AsyncMock(return_value=None) # Default return_value
    # If other methods of session_handler are called by AgentConfigHandler and need mocking, set them up here too.
    # For example, SessionHandler._get_session_path is called by AgentConfigHandler._get_local_agent_configs_base_path
    # This needs to be a regular mock if AgentConfigHandler calls it synchronously on the instance.
    # However, AgentConfigHandler actually calls getattr(self.session_handler, '_get_session_path')(session_id)
    # This is problematic. AgentConfigHandler should use a public interface of SessionHandler.
    # For now, let's assume SessionHandler provides a public get_local_agent_configs_path which is async.
    # Based on previous SessionHandler edit, it's get_local_agent_configs_path(self, session_id: uuid.UUID) -> Path (async)
    mocked_session_handler_for_ach_tests.get_local_agent_configs_path = AsyncMock()
    # And _validate_session_id_format is also called via getattr.
    # This should also be part of a public interface or handled internally by SessionHandler.
    # If AgentConfigHandler calls _validate_session_id_format directly, it should be mocked:
    # mocked_session_handler_for_ach_tests._validate_session_id_format = mock.Mock() # Not async


@pytest.fixture
def handler(tmp_path: Path) -> AgentConfigHandler:
    # Create a distinct Settings instance for these unit tests to avoid conflicts
    # with global patching done in integration tests.
    ach_unit_test_settings = AppSettings(
        WORK_SESSIONS_DIR=tmp_path / "ach_unit_test_work_sessions",
        # GLOBAL_AGENT_CONFIGS_DIR_NAME is taken from the default in Settings model
        # Explicitly set ACP_BASE_DIR as well if WORK_SESSIONS_DIR is not absolute or needs a specific root
        ACP_BASE_DIR=tmp_path # Ensures WORK_SESSIONS_DIR is resolved correctly if it's relative
    )
    # Ensure the paths for this specific settings instance exist
    ach_unit_test_settings.WORK_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    # Use the property GLOBAL_AGENT_CONFIGS_DIR directly
    ach_unit_test_settings.GLOBAL_AGENT_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    
    test_handler = AgentConfigHandler(
        session_handler_instance=mocked_session_handler_for_ach_tests,
        settings_override=ach_unit_test_settings 
    )
    # Assert against the property
    assert test_handler.global_configs_base_path == ach_unit_test_settings.GLOBAL_AGENT_CONFIGS_DIR
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


def mock_session_paths_for_ach_tests(session_uuid: uuid.UUID, tmp_path: Path, session_exists: bool = True):
    session_id_str = str(session_uuid)
    session_base_path_for_test = tmp_path / "sessions_root_for_ach" 
    session_folder = session_base_path_for_test / session_id_str
    
    # Configure the get_local_agent_configs_path mock directly
    local_agents_dir = session_folder / SESSION_AGENTS_DIRNAME
    mocked_session_handler_for_ach_tests.get_local_agent_configs_path.return_value = local_agents_dir

    if session_exists:
        metadata = SessionMetadata(
            id=session_uuid, name="Test Session", 
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc)
        )
        mocked_session_handler_for_ach_tests.get_session_metadata.return_value = metadata
        # AgentConfigHandler will call session_handler.get_local_agent_configs_path,
        # which should create the directory. So we don't create it here explicitly in the mock setup.
        # If the actual implementation of get_local_agent_configs_path (async) in SessionHandler creates it, that's fine.
    else:
        mocked_session_handler_for_ach_tests.get_session_metadata.return_value = None
    # _validate_session_id_format is internal to SessionHandler, AgentConfigHandler should not call it.
    # If it must, it would need to be mocked: mocked_session_handler_for_ach_tests._validate_session_id_format.return_value = None

@pytest.mark.asyncio
async def test_save_and_get_local_agent_config(handler: AgentConfigHandler, tmp_path: Path):
    session_uuid = uuid.uuid4() # Use actual UUID
    agent_id = str(uuid.uuid4())
    mock_session_paths_for_ach_tests(session_uuid, tmp_path, session_exists=True)

    config_data = AgentConfig(agent_id=agent_id, name="Local Agent", agent_type="CodeAgent", llm_model_id="local-llm")
    await handler.save_local_agent_config(str(session_uuid), config_data) # ACH expects str session_id for now

    # The path is now taken from the mocked get_local_agent_configs_path
    expected_local_agents_dir = mocked_session_handler_for_ach_tests.get_local_agent_configs_path.return_value
    expected_file = expected_local_agents_dir / f"{agent_id}.json"
    assert await asyncio.to_thread(expected_file.exists)

    retrieved_config = await handler.get_local_agent_config(str(session_uuid), agent_id)
    assert retrieved_config is not None
    assert retrieved_config.agent_id == agent_id
    assert retrieved_config.created_at == retrieved_config.updated_at

@pytest.mark.asyncio
async def test_get_local_agent_config_session_not_found_returns_none(handler: AgentConfigHandler, tmp_path: Path):
    session_uuid = uuid.uuid4()
    agent_id = str(uuid.uuid4())
    mock_session_paths_for_ach_tests(session_uuid, tmp_path, session_exists=False)
    result = await handler.get_local_agent_config(str(session_uuid), agent_id)
    assert result is None

@pytest.mark.asyncio
async def test_save_local_agent_config_session_not_found(handler: AgentConfigHandler):
    session_uuid = uuid.uuid4()
    agent_id = str(uuid.uuid4())
    # Setup the mock for get_session_metadata to return None for this specific UUID
    mocked_session_handler_for_ach_tests.get_session_metadata.return_value = None
        
    config_data = AgentConfig(agent_id=agent_id, name="Local Agent", agent_type="CodeAgent", llm_model_id="local-llm")
    with pytest.raises(FileNotFoundError, match=f"Work Session ID '{str(session_uuid)}' not found"):
        await handler.save_local_agent_config(str(session_uuid), config_data)

@pytest.mark.asyncio
async def test_list_local_agent_configs(handler: AgentConfigHandler, tmp_path: Path):
    session_uuid = uuid.uuid4()
    mock_session_paths_for_ach_tests(session_uuid, tmp_path, session_exists=True)
    
    local_agents_dir = mocked_session_handler_for_ach_tests.get_local_agent_configs_path.return_value
    # Ensure the directory exists for globbing, as AgentConfigHandler._write_agent_config_file creates it.
    # In a real scenario, save_local_agent_config would have created it.
    # For list, we need it to exist if we expect to find files.
    await asyncio.to_thread(local_agents_dir.mkdir, parents=True, exist_ok=True)
    
    # Clear any existing dummy files if needed (though mock setup should handle this)
    for item in await asyncio.to_thread(list, local_agents_dir.glob("*.json")): 
        await asyncio.to_thread(item.unlink)

    ids = [str(uuid.uuid4()) for _ in range(2)]
    config1 = AgentConfig(agent_id=ids[0], name="Local1", agent_type="CodeAgent", llm_model_id="llm1")
    await handler.save_local_agent_config(str(session_uuid), config1)
    await asyncio.sleep(0.05) 
    config2 = AgentConfig(agent_id=ids[1], name="Local2", agent_type="ToolAgent", llm_model_id="llm2")
    await handler.save_local_agent_config(str(session_uuid), config2)

    listed_configs = await handler.list_local_agent_configs(str(session_uuid))
    assert len(listed_configs) == 2
    assert listed_configs[0].name == "Local2" 
    assert listed_configs[1].name == "Local1"

@pytest.mark.asyncio
async def test_list_local_configs_no_agents_dir(handler: AgentConfigHandler, tmp_path: Path):
    session_uuid = uuid.uuid4()
    mock_session_paths_for_ach_tests(session_uuid, tmp_path, session_exists=True)
    
    local_agents_dir = mocked_session_handler_for_ach_tests.get_local_agent_configs_path.return_value
    if await asyncio.to_thread(local_agents_dir.exists):
        await asyncio.to_thread(shutil.rmtree, local_agents_dir)
    
    # get_session_metadata should indicate session exists for this test path
    metadata = SessionMetadata(id=session_uuid, name="s",created_at=datetime.datetime.now(datetime.timezone.utc),updated_at=datetime.datetime.now(datetime.timezone.utc))
    mocked_session_handler_for_ach_tests.get_session_metadata.return_value = metadata
    
    listed_configs = await handler.list_local_agent_configs(str(session_uuid))
    assert listed_configs == []

@pytest.mark.asyncio
async def test_delete_local_agent_config(handler: AgentConfigHandler, tmp_path: Path):
    session_uuid = uuid.uuid4()
    agent_id = str(uuid.uuid4())
    mock_session_paths_for_ach_tests(session_uuid, tmp_path, session_exists=True)
    
    config_data = AgentConfig(agent_id=agent_id, name="LocalToDelete", agent_type="CodeAgent", llm_model_id="llm-del")
    await handler.save_local_agent_config(str(session_uuid), config_data)
    
    expected_local_agents_dir = mocked_session_handler_for_ach_tests.get_local_agent_configs_path.return_value
    expected_file = expected_local_agents_dir / f"{agent_id}.json"
    assert await asyncio.to_thread(expected_file.exists)

    assert await handler.delete_local_agent_config(str(session_uuid), agent_id) is True
    assert not await asyncio.to_thread(expected_file.exists)
    assert await handler.get_local_agent_config(str(session_uuid), agent_id) is None

@pytest.mark.asyncio
async def test_get_effective_agent_config_global_only(handler: AgentConfigHandler, tmp_path: Path):
    global_agent_id = str(uuid.uuid4())
    global_config = AgentConfig(agent_id=global_agent_id, name="EffectiveGlobal", agent_type="CodeAgent", llm_model_id="g-llm")
    await handler.save_global_agent_config(global_config)
    
    mocked_session_handler_for_ach_tests.get_session_metadata.return_value = None # No local session
    retrieved = await handler.get_effective_agent_config(global_agent_id)
    assert retrieved is not None; assert retrieved.name == "EffectiveGlobal"
    
    session_uuid = uuid.uuid4() # A session that exists but has no local config for this agent
    mock_session_paths_for_ach_tests(session_uuid, tmp_path, session_exists=True)
    # Ensure get_local_agent_config returns None for this specific combo
    # The mock_session_paths_for_ach_tests will set up get_session_metadata to return a session.
    # We need to ensure that get_local_agent_config (which internally calls _read_agent_config_file)
    # returns None because the file won't exist.
    # This is implicitly tested if the global one is picked up.
    
    retrieved_with_session = await handler.get_effective_agent_config(global_agent_id, str(session_uuid))
    assert retrieved_with_session is not None; assert retrieved_with_session.name == "EffectiveGlobal"

@pytest.mark.asyncio
async def test_get_effective_agent_config_local_overrides_global(handler: AgentConfigHandler, tmp_path: Path):
    agent_id = str(uuid.uuid4())
    session_uuid = uuid.uuid4()
    mock_session_paths_for_ach_tests(session_uuid, tmp_path, session_exists=True)

    global_config = AgentConfig(agent_id=agent_id, name="GlobalNameToOverride", agent_type="CodeAgent", llm_model_id="g-llm")
    await handler.save_global_agent_config(global_config)

    local_config = AgentConfig(agent_id=agent_id, name="LocalOverrides", agent_type="CodeAgent", llm_model_id="l-llm")
    await handler.save_local_agent_config(str(session_uuid), local_config)

    retrieved = await handler.get_effective_agent_config(agent_id, str(session_uuid))
    assert retrieved is not None
    assert retrieved.name == "LocalOverrides"
    assert retrieved.llm_model_id == "l-llm"

@pytest.mark.asyncio
async def test_get_effective_agent_config_local_only(handler: AgentConfigHandler, tmp_path: Path):
    agent_id = str(uuid.uuid4())
    session_uuid = uuid.uuid4()
    mock_session_paths_for_ach_tests(session_uuid, tmp_path, session_exists=True)

    # Ensure no global config for this agent_id
    await handler.delete_global_agent_config(agent_id) # delete if it exists from a previous failed run

    local_config = AgentConfig(agent_id=agent_id, name="EffectiveLocalOnly", agent_type="CodeAgent", llm_model_id="l-llm-only")
    await handler.save_local_agent_config(str(session_uuid), local_config)

    retrieved = await handler.get_effective_agent_config(agent_id, str(session_uuid))
    assert retrieved is not None
    assert retrieved.name == "EffectiveLocalOnly"

    # Test case where session_id is None but local config exists (should not happen with current ACH logic, but good to be robust)
    # This will effectively try to get global, which doesn't exist.
    retrieved_no_session = await handler.get_effective_agent_config(agent_id) 
    assert retrieved_no_session is None # Expect None as no global config exists


@pytest.mark.asyncio
async def test_list_empty_global_configs(handler: AgentConfigHandler, tmp_path: Path): 
    for item in handler.global_configs_base_path.glob("*.json"): 
        await asyncio.to_thread(item.unlink)
    assert await handler.list_global_agent_configs() == []

@pytest.mark.asyncio
async def test_delete_non_existent_global_config(handler: AgentConfigHandler): 
    assert await handler.delete_global_agent_config(str(uuid.uuid4())) is False

@pytest.mark.asyncio
async def test_invalid_agent_id_operations(handler: AgentConfigHandler): 
    invalid_ids = [r"../escape", r"path/slash", r"path\\slash", r""]
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
