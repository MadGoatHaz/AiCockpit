import pytest
from pydantic import ValidationError
import datetime

from acp_backend.models.work_board_models import (
    FileNode, ReadFileResponse, WriteFileRequest,
    CreateDirectoryRequest, MoveItemRequest, ListDirRequest
)

# --- FileNode Tests ---
def test_file_node_valid_file():
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    data = {
        "name": "test_file.txt", "path": "project_a/test_file.txt", "is_dir": False,
        "size_bytes": 1024, "modified_at": now_iso
    }
    node = FileNode(**data)
    assert node.name == data["name"]
    assert node.size_bytes == 1024
    assert node.modified_at == now_iso
    print(f"\n[PASSED] test_file_node_valid_file")

def test_file_node_valid_directory():
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    data = {
        "name": "project_a", "path": "project_a", "is_dir": True,
        "modified_at": now_iso # size_bytes is None for dir
    }
    node = FileNode(**data)
    assert node.is_dir is True
    assert node.size_bytes is None
    assert node.modified_at == now_iso
    print(f"\n[PASSED] test_file_node_valid_directory")

@pytest.mark.parametrize("field, value, error_type_part", [
    ("name", "", "string_too_short"),
    ("size_bytes", -100, "greater_than_equal"),
])
def test_file_node_invalid_constraints(field, value, error_type_part):
    valid_data = {
        "name": "valid_item", "path": "valid_item", "is_dir": False,
        "modified_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    # Ensure size_bytes is set if not the field being tested for negativity
    if field != "size_bytes":
        valid_data["size_bytes"] = 100

    invalid_data = valid_data.copy()
    invalid_data[field] = value
    
    with pytest.raises(ValidationError) as excinfo:
        FileNode(**invalid_data)
    
    print(f"\nDEBUG: For FileNode {field}='{value}', errors: {excinfo.value.errors()}")
    found_error = any(
        error.get('loc') and field == error['loc'][0] and error_type_part in error.get('type', '')
        for error in excinfo.value.errors()
    )
    assert found_error, f"Expected error for {field} with type part {error_type_part}"
    print(f"\n[PASSED] test_file_node_invalid_constraints for {field}={value}")

def test_file_node_extra_fields_forbidden():
    data = {
        "name": "test", "path": "test", "is_dir": False, 
        "modified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "extra_field": "bad"
    }
    with pytest.raises(ValidationError):
        FileNode(**data)
    print(f"\n[PASSED] test_file_node_extra_fields_forbidden")


# --- ListDirRequest Tests (even if unused by router, model should be valid) ---
def test_list_dir_request_default_path():
    req = ListDirRequest()
    assert req.path == "."
    print(f"\n[PASSED] test_list_dir_request_default_path")

def test_list_dir_request_custom_path():
    req = ListDirRequest(path="some/folder")
    assert req.path == "some/folder"
    print(f"\n[PASSED] test_list_dir_request_custom_path")


# --- ReadFileResponse Tests ---
def test_read_file_response_valid():
    resp = ReadFileResponse(path="file.txt", content="Hello", encoding="ascii")
    assert resp.path == "file.txt"
    assert resp.content == "Hello"
    assert resp.encoding == "ascii"
    print(f"\n[PASSED] test_read_file_response_valid")


# --- WriteFileRequest Tests ---
def test_write_file_request_valid():
    req = WriteFileRequest(path="new.txt", content="World", encoding="utf-16")
    assert req.path == "new.txt"
    assert req.content == "World"
    assert req.encoding == "utf-16"
    print(f"\n[PASSED] test_write_file_request_valid")


# --- CreateDirectoryRequest Tests ---
def test_create_directory_request_valid():
    req = CreateDirectoryRequest(path="new_dir/subdir")
    assert req.path == "new_dir/subdir"
    print(f"\n[PASSED] test_create_directory_request_valid")


# --- MoveItemRequest Tests ---
def test_move_item_request_valid():
    req = MoveItemRequest(source_path="old/item", destination_path="new/location/item_new_name")
    assert req.source_path == "old/item"
    assert req.destination_path == "new/location/item_new_name"
    print(f"\n[PASSED] test_move_item_request_valid")

