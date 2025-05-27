# <PROJECT_ROOT>/tests/unit/core/test_session_handler.py
import pytest
import os
import shutil
import json 
import uuid 
import datetime 
from unittest import mock

from acp_backend.config import settings as app_settings
from acp_backend.core.session_handler import SessionHandler, SESSION_MANIFEST_FILENAME, SESSION_DATA_DIRNAME
from acp_backend.models.work_session_models import CreateWorkSessionRequest

TEST_SESSIONS_BASE_DIR = "./test_acp_work_sessions"

@pytest.fixture(autouse=True)
def manage_test_sessions_dir_auto():
    """Fixture to set WORK_SESSIONS_DIR and clean up TEST_SESSIONS_BASE_DIR."""
    # Clean up before test run starts for this module/session
    if os.path.exists(TEST_SESSIONS_BASE_DIR):
        shutil.rmtree(TEST_SESSIONS_BASE_DIR)
    # Individual tests will handle creation of TEST_SESSIONS_BASE_DIR if SessionHandler.__init__ is SUT
    
    with mock.patch.object(app_settings, 'WORK_SESSIONS_DIR', TEST_SESSIONS_BASE_DIR):
        yield 

    # Clean up after all tests in the module might have run
    if os.path.exists(TEST_SESSIONS_BASE_DIR):
        shutil.rmtree(TEST_SESSIONS_BASE_DIR)

# Test __init__
def test_session_handler_init_success():
    """Test SessionHandler initialization successfully creates base directory."""
    if os.path.exists(TEST_SESSIONS_BASE_DIR): # Ensure clean slate for this specific test
        shutil.rmtree(TEST_SESSIONS_BASE_DIR)
    
    handler = SessionHandler() # This should create TEST_SESSIONS_BASE_DIR
    assert os.path.exists(TEST_SESSIONS_BASE_DIR)
    assert handler.sessions_base_dir == TEST_SESSIONS_BASE_DIR
    print(f"\n[PASSED] test_session_handler_init_success")

@mock.patch('acp_backend.core.session_handler.os.makedirs')
def test_session_handler_init_failure_os_error(mock_os_makedirs_init):
    """Test SessionHandler init raises RuntimeError if base directory creation fails."""
    mock_os_makedirs_init.side_effect = OSError("Init Permission denied")
    
    with pytest.raises(RuntimeError) as excinfo:
        SessionHandler() 
    
    assert "SessionHandler critical failure" in str(excinfo.value)
    assert "Init Permission denied" in str(excinfo.value)
    mock_os_makedirs_init.assert_called_once_with(TEST_SESSIONS_BASE_DIR, exist_ok=True)
    print(f"\n[PASSED] test_session_handler_init_failure_os_error")

# --- create_session Tests ---

@mock.patch('acp_backend.core.session_handler.datetime')
@mock.patch('acp_backend.core.session_handler.uuid')
@mock.patch('acp_backend.core.session_handler.os.makedirs') 
@mock.patch('acp_backend.core.session_handler.open', new_callable=mock.mock_open)
@mock.patch('acp_backend.core.session_handler.json.dump')
async def test_create_session_success(
    mock_json_dump, mock_file_open, mock_os_makedirs_cs, mock_uuid_cs, mock_datetime_cs
):
    """Test successful session creation."""
    # Ensure TEST_SESSIONS_BASE_DIR exists for SessionHandler() init to use real os.makedirs
    # or a non-failing mock if SessionHandler.__init__ itself is not the SUT for this test.
    if not os.path.exists(TEST_SESSIONS_BASE_DIR):
        os.makedirs(TEST_SESSIONS_BASE_DIR, exist_ok=True)

    mock_uuid_cs.uuid4.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
    fixed_now_dt = datetime.datetime(2023, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
    mock_datetime_cs.datetime.now.return_value = fixed_now_dt 
    
    # The mock_os_makedirs_cs is active due to the decorator.
    # The call in SessionHandler's __init__ will use it.
    # The calls in create_session() will also use it.
    # We reset the mock after SessionHandler() instantiation to isolate calls for create_session.
    
    handler = SessionHandler() 
    mock_os_makedirs_cs.reset_mock() # Reset after __init__ call

    request_data = CreateWorkSessionRequest(name="Test Session", description="A test description.")
    created_session = await handler.create_session(request_data)

    expected_session_id = "12345678-1234-5678-1234-567812345678"
    expected_session_folder = os.path.join(TEST_SESSIONS_BASE_DIR, expected_session_id)
    expected_data_folder = os.path.join(expected_session_folder, SESSION_DATA_DIRNAME)
    expected_manifest_path = os.path.join(expected_session_folder, SESSION_MANIFEST_FILENAME)

    assert created_session.session_id == expected_session_id
    assert created_session.name == "Test Session"
    assert created_session.description == "A test description."
    assert created_session.created_at == fixed_now_dt.isoformat() 
    assert created_session.last_accessed == fixed_now_dt.isoformat()

    # These are the calls expected from within create_session()
    expected_makedirs_calls_in_create = [
        mock.call(expected_session_folder, exist_ok=False),
        mock.call(expected_data_folder, exist_ok=True)
    ]
    mock_os_makedirs_cs.assert_has_calls(expected_makedirs_calls_in_create, any_order=False)
    assert mock_os_makedirs_cs.call_count == 2 # Only count calls from create_session

    mock_file_open.assert_called_once_with(expected_manifest_path, "w", encoding="utf-8")
    mock_json_dump.assert_called_once()
    dumped_data = mock_json_dump.call_args[0][0]
    assert dumped_data["session_id"] == expected_session_id
    assert dumped_data["name"] == "Test Session"
    
    print(f"\n[PASSED] test_create_session_success")

@mock.patch('acp_backend.core.session_handler.datetime')
@mock.patch('acp_backend.core.session_handler.uuid')
@mock.patch('acp_backend.core.session_handler.os.makedirs') 
@mock.patch('acp_backend.core.session_handler.open', new_callable=mock.mock_open)
@mock.patch('acp_backend.core.session_handler.json.dump', side_effect=IOError("Failed to write manifest"))
@mock.patch('acp_backend.core.session_handler.shutil.rmtree')
@mock.patch('acp_backend.core.session_handler.os.path.exists') 
async def test_create_session_manifest_write_failure_cleanup(
    mock_os_path_exists_cl, mock_shutil_rmtree_cl, mock_json_dump_failure_cl, 
    mock_file_open_cl, mock_os_makedirs_cl, mock_uuid_cl, mock_datetime_cl
):
    """Test cleanup occurs if writing session manifest fails."""
    if not os.path.exists(TEST_SESSIONS_BASE_DIR): # Ensure base dir for SessionHandler init
         os.makedirs(TEST_SESSIONS_BASE_DIR, exist_ok=True)

    mock_uuid_cl.uuid4.return_value = uuid.UUID('12345678-1234-1234-1234-1234567890ab') 
    mock_datetime_cl.datetime.now.return_value = datetime.datetime(2023,1,1,12,0,0, tzinfo=datetime.timezone.utc)
    
    handler = SessionHandler() # __init__ call to os.makedirs uses mock_os_makedirs_cl
    mock_os_makedirs_cl.reset_mock() # Reset for calls within create_session

    # Configure os.path.exists for the cleanup check
    expected_session_id = "12345678-1234-1234-1234-1234567890ab"
    expected_session_folder = os.path.join(TEST_SESSIONS_BASE_DIR, expected_session_id)
    # Make os.path.exists return True specifically for the session folder to test rmtree call
    mock_os_path_exists_cl.side_effect = lambda path_arg: path_arg == expected_session_folder

    request_data = CreateWorkSessionRequest(name="Cleanup Test", description="Test manifest failure.")

    with pytest.raises(RuntimeError) as excinfo:
        await handler.create_session(request_data)
    
    assert "Could not write session manifest" in str(excinfo.value)
    assert "Failed to write manifest" in str(excinfo.value)
    
    mock_shutil_rmtree_cl.assert_called_once_with(expected_session_folder)
    print(f"\n[PASSED] test_create_session_manifest_write_failure_cleanup")

@mock.patch('acp_backend.core.session_handler.uuid') 
async def test_create_session_folder_already_exists(mock_uuid_fe):
    """Test behavior if session folder (UUID collision) already exists."""
    # SessionHandler.__init__ should succeed using real os.makedirs.
    # The fixture ensures TEST_SESSIONS_BASE_DIR is clean, then __init__ creates it.
    if not os.path.exists(TEST_SESSIONS_BASE_DIR):
         os.makedirs(TEST_SESSIONS_BASE_DIR, exist_ok=True)
        
    handler = SessionHandler() 
    
    fixed_uuid_str = 'abcdef01-abcd-ef01-abcd-ef0123456789'
    mock_uuid_fe.uuid4.return_value = uuid.UUID(fixed_uuid_str)
    expected_session_folder = os.path.join(TEST_SESSIONS_BASE_DIR, fixed_uuid_str)

    request_data = CreateWorkSessionRequest(name="Collision Test", description="Test folder exists.")

    # We want to mock os.makedirs ONLY for the scope of handler.create_session
    # and specifically for the call that creates the session folder.
    with mock.patch('acp_backend.core.session_handler.os.makedirs') as mock_makedirs_inner_create:
        # 1st call (session folder) from create_session: Raise FileExistsError
        # 2nd call (data_folder) from create_session: Should not happen, but mock to allow.
        mock_makedirs_inner_create.side_effect = [
            FileExistsError("Session folder already exists"), 
            None 
        ]

        with pytest.raises(RuntimeError) as excinfo:
            await handler.create_session(request_data)
            
    assert "already exists (UUID collision?)" in str(excinfo.value)
    
    # Check the calls to the inner mock (mock_makedirs_inner_create)
    # This mock is *only* active during the create_session call.
    mock_makedirs_inner_create.assert_called_once_with(expected_session_folder, exist_ok=False)
    print(f"\n[PASSED] test_create_session_folder_already_exists")
