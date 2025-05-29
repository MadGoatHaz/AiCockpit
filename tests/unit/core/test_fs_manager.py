# <PROJECT_ROOT>/tests/unit/core/test_fs_manager.py
import pytest
import os
import shutil
import datetime
from pathlib import Path 
from unittest import mock
import asyncio 

from acp_backend.core.fs_manager import FileSystemManager 
from acp_backend.models.work_board_models import WriteFileRequest, FileNode 
from acp_backend.core.session_handler import SessionHandler as SessionHandlerClass, SESSION_DATA_DIRNAME # Import SESSION_DATA_DIRNAME


@pytest.fixture(scope="module")
def module_tmp_sessions_path(tmp_path_factory):
    return tmp_path_factory.mktemp("fs_manager_module_sessions_unit")

@pytest.fixture
def fsm_instance_with_patched_session_handler(module_tmp_sessions_path):
    mock_sh = mock.Mock(spec=SessionHandlerClass) 
    
    def mock_get_session_data_path(session_id):
        # This mock needs to create the directory *if the test expects it to exist*
        # The FSM init/tests should handle its creation via _get_session_data_root calling it.
        session_data_dir = module_tmp_sessions_path / session_id / SESSION_DATA_DIRNAME
        return session_data_dir

    def mock_validate_session_id_format(session_id):
        if not session_id or ".." in session_id or "/" in session_id or "\\" in session_id:
            raise ValueError("Invalid session_id format")
        return None

    def mock_get_session_folder_path(session_id):
        mock_validate_session_id_format(session_id) 
        # For FSManager tests, we need these paths to be actual Path objects for resolve() and exists()
        return module_tmp_sessions_path / session_id

    mock_sh._get_session_data_path.side_effect = mock_get_session_data_path
    mock_sh._validate_session_id_format.side_effect = mock_validate_session_id_format
    mock_sh._get_session_path.side_effect = mock_get_session_folder_path
    
    # Instantiate FileSystemManager with the mocked SessionHandler
    fsm = FileSystemManager(session_handler_instance=mock_sh)
    
    yield fsm


@pytest.fixture
def test_session(fsm_instance_with_patched_session_handler: FileSystemManager, module_tmp_sessions_path):
    fsm = fsm_instance_with_patched_session_handler
    session_id = "test_session_for_fs_unit"
    
    # Manually create the session structure expected by _get_session_data_root
    session_data_dir = module_tmp_sessions_path / session_id / SESSION_DATA_DIRNAME
    session_data_dir.mkdir(parents=True, exist_ok=True) 

    (session_data_dir / "file1.txt").write_text("content1")
    subdir1 = (session_data_dir / "subdir1")
    subdir1.mkdir(exist_ok=True)
    (subdir1 / "file2.txt").write_text("content2")
    
    return session_id, session_data_dir, fsm


@pytest.mark.asyncio
async def test_list_dir_root(test_session):
    session_id, session_data_dir, fsm = test_session
    nodes = await fsm.list_dir(session_id, ".")
    assert len(nodes) == 2
    names = sorted([node.name for node in nodes])
    assert names == ["file1.txt", "subdir1"]

@pytest.mark.asyncio
async def test_list_dir_subdir(test_session):
    session_id, _, fsm = test_session
    nodes = await fsm.list_dir(session_id, "subdir1")
    assert len(nodes) == 1; assert nodes[0].name == "file2.txt"

@pytest.mark.asyncio
async def test_list_dir_non_existent(test_session):
    session_id, _, fsm = test_session
    with pytest.raises(FileNotFoundError): await fsm.list_dir(session_id, "non_existent_dir")

@pytest.mark.asyncio
async def test_read_file_success(test_session):
    session_id, _, fsm = test_session
    response = await fsm.read_file(session_id, "file1.txt")
    assert response.content == "content1"

@pytest.mark.asyncio
async def test_read_file_not_found(test_session):
    session_id, _, fsm = test_session
    with pytest.raises(FileNotFoundError): await fsm.read_file(session_id, "not_found.txt")

@pytest.mark.asyncio
async def test_read_file_is_directory(test_session):
    session_id, _, fsm = test_session
    with pytest.raises(IsADirectoryError): await fsm.read_file(session_id, "subdir1")

@pytest.mark.asyncio
async def test_write_file_create_new(test_session):
    session_id, session_data_dir, fsm = test_session
    req = WriteFileRequest(path="new_file.txt", content="new content")
    created_file_node = await fsm.write_file(session_id, req)
    assert (session_data_dir / "new_file.txt").read_text() == "new content"
    assert created_file_node.name == "new_file.txt"
    assert created_file_node.path == "new_file.txt"
    assert not created_file_node.is_dir
    assert created_file_node.size_bytes is not None

@pytest.mark.asyncio
async def test_delete_item_file(test_session):
    session_id, session_data_dir, fsm = test_session
    assert await fsm.delete_item(session_id, "file1.txt") is True
    assert not (session_data_dir / "file1.txt").exists()

@pytest.mark.asyncio
async def test_create_directory_success(test_session):
    session_id, session_data_dir, fsm = test_session
    created_dir_node = await fsm.create_directory(session_id, "new_created_dir")
    assert (session_data_dir / "new_created_dir").is_dir()
    assert created_dir_node.name == "new_created_dir"
    assert created_dir_node.path == "new_created_dir"
    assert created_dir_node.is_dir
    assert created_dir_node.size_bytes is None


@pytest.mark.asyncio
async def test_path_traversal_protection_list_dir(test_session):
    session_id, _, fsm = test_session
    with pytest.raises(FileNotFoundError, match="Access denied"): 
        await fsm.list_dir(session_id, "../another_session")

@pytest.mark.asyncio
async def test_write_file_overwrite_existing(test_session):
    session_id, session_data_dir, fsm = test_session
    req = WriteFileRequest(path="file1.txt", content="overwritten content")
    updated_file_node = await fsm.write_file(session_id, req)
    assert (session_data_dir / "file1.txt").read_text() == "overwritten content"
    assert updated_file_node.name == "file1.txt"
    assert updated_file_node.path == "file1.txt"

@pytest.mark.asyncio
async def test_create_directory_path_is_file(test_session):
    session_id, _, fsm = test_session
    with pytest.raises(FileExistsError):
        await fsm.create_directory(session_id, "file1.txt")

@pytest.mark.asyncio
async def test_move_item_file_success(test_session):
    session_id, session_data_dir, fsm = test_session
    source_path = "file1.txt"
    destination_path = "new_location/moved_file.txt"
    
    (session_data_dir / "new_location").mkdir(parents=True, exist_ok=True)

    moved_node = await fsm.move_item(session_id, source_path, destination_path)

    assert not (session_data_dir / source_path).exists()
    assert (session_data_dir / destination_path).exists()
    assert (session_data_dir / destination_path).read_text() == "content1"
    assert moved_node.name == "moved_file.txt"
    assert moved_node.path == destination_path

@pytest.mark.asyncio
async def test_move_item_directory_success(test_session):
    session_id, session_data_dir, fsm = test_session
    source_path = "subdir1"
    destination_path = "new_subdir/renamed_subdir"
    
    (session_data_dir / "new_subdir").mkdir(parents=True, exist_ok=True)

    moved_node = await fsm.move_item(session_id, source_path, destination_path)

    assert not (session_data_dir / source_path).exists()
    assert (session_data_dir / destination_path).is_dir()
    assert (session_data_dir / destination_path / "file2.txt").exists()
    assert moved_node.name == "renamed_subdir"
    assert moved_node.path == destination_path
    assert moved_node.is_dir
