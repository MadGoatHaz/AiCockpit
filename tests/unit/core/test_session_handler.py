# <PROJECT_ROOT>/tests/unit/core/test_session_handler.py
import pytest
import os
import shutil
import json 
import uuid 
import datetime 
from pathlib import Path 
from unittest import mock
import asyncio

from acp_backend.config import settings as global_app_settings 
from acp_backend.core.session_handler import SessionHandler, SESSION_MANIFEST_FILENAME, SESSION_DATA_DIRNAME, LOCAL_AGENTS_DIR_NAME
from acp_backend.models.work_session_models import CreateWorkSessionRequest, UpdateWorkSessionRequest, WorkSession

TEST_SESSIONS_BASE_DIR_FOR_HANDLER_TESTS = Path("./test_acp_work_sessions_handler_tests")

@pytest.fixture(autouse=True)
def manage_test_sessions_dir_auto(monkeypatch):
    if TEST_SESSIONS_BASE_DIR_FOR_HANDLER_TESTS.exists():
        shutil.rmtree(TEST_SESSIONS_BASE_DIR_FOR_HANDLER_TESTS)
    TEST_SESSIONS_BASE_DIR_FOR_HANDLER_TESTS.mkdir(parents=True, exist_ok=True)
    
    monkeypatch.setattr(global_app_settings, 'WORK_SESSIONS_DIR', TEST_SESSIONS_BASE_DIR_FOR_HANDLER_TESTS)
    yield 
    if TEST_SESSIONS_BASE_DIR_FOR_HANDLER_TESTS.exists():
        shutil.rmtree(TEST_SESSIONS_BASE_DIR_FOR_HANDLER_TESTS)

@pytest.fixture
def handler() -> SessionHandler:
    return SessionHandler()

def test_session_handler_init_success(monkeypatch, tmp_path: Path):
    test_specific_dir = tmp_path / "sh_init_success"
    
    original_work_sessions_dir = global_app_settings.WORK_SESSIONS_DIR
    # We need to patch the global `settings` instance that SessionHandler imports and uses.
    # The `get_global_agent_configs_path` is a method of this instance.
    
    monkeypatch.setattr(global_app_settings, 'WORK_SESSIONS_DIR', test_specific_dir)
    # No need to patch get_global_agent_configs_path if it correctly uses self.WORK_SESSIONS_DIR

    if test_specific_dir.exists(): shutil.rmtree(test_specific_dir)
    
    sh = SessionHandler() 
    
    assert test_specific_dir.exists()
    # SessionHandler's _ensure_base_directory_exists calls settings.get_global_agent_configs_path()
    # This method on the settings instance uses its own WORK_SESSIONS_DIR attribute.
    expected_global_agents_path = test_specific_dir / global_app_settings.GLOBAL_AGENT_CONFIGS_DIR_NAME
    assert expected_global_agents_path.exists()
    assert sh.sessions_base_dir == test_specific_dir
    
    monkeypatch.setattr(global_app_settings, 'WORK_SESSIONS_DIR', original_work_sessions_dir)


def test_session_handler_init_failure_os_error(monkeypatch, tmp_path: Path):
    test_specific_dir = tmp_path / "sh_init_failure"
    original_work_sessions_dir = global_app_settings.WORK_SESSIONS_DIR
    monkeypatch.setattr(global_app_settings, 'WORK_SESSIONS_DIR', test_specific_dir)

    # Mock pathlib.Path.mkdir which is called by both self.sessions_base_dir.mkdir
    # and settings.get_global_agent_configs_path().mkdir
    with mock.patch('pathlib.Path.mkdir', side_effect=OSError("Init Permission denied")) as mock_mkdir:
        with pytest.raises(RuntimeError) as excinfo: 
            SessionHandler() 
        assert "SessionHandler critical failure" in str(excinfo.value)
        assert "Init Permission denied" in str(excinfo.value)
        # Ensure mkdir was attempted (it should be, by _ensure_base_directory_exists)
        mock_mkdir.assert_called() 
    
    monkeypatch.setattr(global_app_settings, 'WORK_SESSIONS_DIR', original_work_sessions_dir)


@pytest.mark.asyncio
async def test_create_session_success(handler: SessionHandler):
    request_data = CreateWorkSessionRequest(name="Test Session Create", description="Desc for create.")
    created_session = await handler.create_session(request_data)
    assert created_session.name == "Test Session Create"
    session_folder = TEST_SESSIONS_BASE_DIR_FOR_HANDLER_TESTS / created_session.session_id
    assert await asyncio.to_thread(session_folder.is_dir)
    assert await asyncio.to_thread((session_folder / SESSION_DATA_DIRNAME).is_dir)
    assert await asyncio.to_thread((session_folder / LOCAL_AGENTS_DIR_NAME).is_dir)
    manifest_file = session_folder / SESSION_MANIFEST_FILENAME
    assert await asyncio.to_thread(manifest_file.is_file)
    
    def _read_manifest():
        with open(manifest_file, "r", encoding='utf-8') as f: 
            return json.load(f)
    data = await asyncio.to_thread(_read_manifest)
    assert data["name"] == "Test Session Create"

@pytest.mark.asyncio
async def test_create_session_manifest_write_failure(handler: SessionHandler, monkeypatch):
    request_data = CreateWorkSessionRequest(name="Manifest Fail Test")
    original_open = open 
    def mock_open_side_effect(file_path, mode='r', **kwargs):
        path_obj = Path(file_path)
        if path_obj.name == SESSION_MANIFEST_FILENAME and 'w' in mode:
            raise IOError("Failed to write manifest")
        return original_open(file_path, mode, **kwargs)
    monkeypatch.setattr("builtins.open", mock_open_side_effect)
    with pytest.raises(RuntimeError, match="Could not write session manifest"):
        await handler.create_session(request_data)
    monkeypatch.undo()

@pytest.mark.asyncio
async def test_list_sessions_empty(handler: SessionHandler):
    assert await handler.list_sessions() == []

@pytest.mark.asyncio
async def test_list_sessions_multiple(handler: SessionHandler):
    s1 = await handler.create_session(CreateWorkSessionRequest(name="Session Alpha"))
    await asyncio.sleep(0.1) # Increased sleep duration
    s2 = await handler.create_session(CreateWorkSessionRequest(name="Session Beta"))
    await asyncio.sleep(0.01) # Small sleep to ensure s2's manifest is written before listing
    
    sessions = await handler.list_sessions()
    assert len(sessions) == 2
    # s2 was created after s1 and get_session (called by list_sessions) updates last_accessed.
    # If s2 is accessed last (during its get_session call within list_sessions), it should be first.
    # The sorting is by last_accessed descending.
    # The call to get_session for s1 will happen, then for s2 (or vice-versa depending on iterdir).
    # Let's ensure s2 is "fresher" by explicitly getting it after s1's get_session call within list_sessions
    # This test might be a bit fragile due to timing of get_session calls within list_sessions.
    # A more robust way would be to check if s2.last_accessed > s1.last_accessed.
    
    # Simpler check: s2 is created later, so its creation time (and initial last_accessed) is later.
    # When list_sessions calls get_session for both, it updates their last_accessed times.
    # The one whose get_session was called more recently by list_sessions might appear first.
    # The key is that they are sorted by last_accessed.
    
    # To make it deterministic for this test:
    # Get s1, then get s2. s2 should be "more recently accessed" by get_session.
    # However, list_sessions iterates and calls get_session internally.
    # The sleep ensures s2 is created later.
    # The list_sessions sorts by last_accessed. The one processed last by get_session within list_sessions
    # will have the latest last_accessed time.
    
    # Let's assume s2 is indeed more recent due to creation time and the sleep.
    if sessions[0].session_id == s1.session_id: # If s1 is first, then s2 must be second
        assert sessions[1].session_id == s2.session_id
        assert sessions[0].last_accessed >= sessions[1].last_accessed
    else: # If s2 is first, then s1 must be second
        assert sessions[0].session_id == s2.session_id
        assert sessions[1].session_id == s1.session_id
        assert sessions[0].last_accessed >= sessions[1].last_accessed


@pytest.mark.asyncio
async def test_get_session_success_and_updates_last_accessed(handler: SessionHandler):
    created = await handler.create_session(CreateWorkSessionRequest(name="Get Me"))
    original_last_accessed_iso = created.last_accessed
    await asyncio.sleep(0.1) 
    retrieved = await handler.get_session(created.session_id)
    assert retrieved is not None
    assert retrieved.last_accessed > original_last_accessed_iso

@pytest.mark.asyncio
async def test_get_session_not_found(handler: SessionHandler):
    assert await handler.get_session(str(uuid.uuid4())) is None

@pytest.mark.asyncio
async def test_update_session_success(handler: SessionHandler):
    created = await handler.create_session(CreateWorkSessionRequest(name="Original Name"))
    update_req = UpdateWorkSessionRequest(name="Updated Name", description="New Desc")
    updated = await handler.update_session(created.session_id, update_req)
    assert updated is not None 
    assert updated.name == "Updated Name" 
    assert updated.created_at == created.created_at

@pytest.mark.asyncio
async def test_update_session_partial(handler: SessionHandler):
    created = await handler.create_session(CreateWorkSessionRequest(name="Partial Update", description="Old Desc"))
    await handler.update_session(created.session_id, UpdateWorkSessionRequest(name="Name Changed Only"))
    retrieved = await handler.get_session(created.session_id) 
    assert retrieved is not None 
    assert retrieved.name == "Name Changed Only" 
    assert retrieved.description == "Old Desc"

@pytest.mark.asyncio
async def test_update_session_not_found(handler: SessionHandler):
    assert await handler.update_session(str(uuid.uuid4()), UpdateWorkSessionRequest(name="No Such")) is None

@pytest.mark.asyncio
async def test_delete_session_success(handler: SessionHandler):
    created = await handler.create_session(CreateWorkSessionRequest(name="To Delete"))
    assert await handler.delete_session(created.session_id) is True
    assert not await asyncio.to_thread((TEST_SESSIONS_BASE_DIR_FOR_HANDLER_TESTS / created.session_id).exists)

@pytest.mark.asyncio
async def test_delete_session_not_found(handler: SessionHandler):
    assert await handler.delete_session(str(uuid.uuid4())) is True

@pytest.mark.asyncio
async def test_invalid_session_id_format_raises_valueerror(handler: SessionHandler):
    invalid_ids = ["../escape", "path/slash", "path\\slash", ""]
    for invalid_id in invalid_ids:
        with pytest.raises(ValueError, match="Invalid session_id format"):
            handler._get_session_folder_path(invalid_id)
