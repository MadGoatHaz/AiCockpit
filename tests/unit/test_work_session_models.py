# <PROJECT_ROOT>/tests/unit/models/test_work_session_models.py
import pytest
from pydantic import ValidationError

from acp_backend.models.work_session_models import SessionCreate

def test_create_work_session_request_valid():
    """Test successful creation with valid data."""
    data = {
        "name": "Valid Session Name",
        "description": "A valid description for the session."
    }
    req = SessionCreate(**data)
    assert req.name == data["name"]
    assert req.description == data["description"]
    print(f"\n[PASSED] test_create_work_session_request_valid: {req.model_dump_json(indent=2)}")

def test_create_work_session_request_valid_no_description():
    """Test successful creation with valid name and no description."""
    data = {"name": "Session Without Description"}
    req = SessionCreate(**data)
    assert req.name == data["name"]
    assert req.description is None # Default for Optional description is None
    print(f"\n[PASSED] test_create_work_session_request_valid_no_description: {req.model_dump_json(indent=2)}")

def test_create_work_session_request_missing_name():
    """Test ValidationError when 'name' field is missing."""
    data = {"description": "This session is missing a name."}
    with pytest.raises(ValidationError) as excinfo:
        SessionCreate(**data)
    
    assert len(excinfo.value.errors()) == 1
    assert excinfo.value.errors()[0]['type'] == 'missing'
    assert excinfo.value.errors()[0]['loc'] == ('name',)
    print(f"\n[PASSED] test_create_work_session_request_missing_name: Correctly raised ValidationError for missing name.")
    # print(excinfo.value.errors()) # Optional: for more details during debugging

@pytest.mark.parametrize(
    "invalid_name, expected_error_type_part",
    [
        ("", "too_short"),  # Empty name
        ("N" * 101, "too_long"),  # Name too long
    ]
)
def test_create_work_session_request_invalid_name_length(invalid_name, expected_error_type_part):
    """Test ValidationError for invalid 'name' length."""
    data = {
        "name": invalid_name,
        "description": "Testing name length."
    }
    with pytest.raises(ValidationError) as excinfo:
        SessionCreate(**data)
    
    assert len(excinfo.value.errors()) == 1
    # Pydantic v2 error types are like 'string_too_short', 'string_too_long'
    assert expected_error_type_part in excinfo.value.errors()[0]['type']
    assert excinfo.value.errors()[0]['loc'] == ('name',)
    print(f"\n[PASSED] test_create_work_session_request_invalid_name_length (name='{invalid_name}'): Correctly raised ValidationError.")

def test_create_work_session_request_invalid_description_length():
    """Test ValidationError for invalid 'description' length."""
    data = {
        "name": "Valid Name",
        "description": "D" * 501  # Description too long
    }
    with pytest.raises(ValidationError) as excinfo:
        SessionCreate(**data)
    
    assert len(excinfo.value.errors()) == 1
    assert "too_long" in excinfo.value.errors()[0]['type'] # 'string_too_long'
    assert excinfo.value.errors()[0]['loc'] == ('description',)
    print(f"\n[PASSED] test_create_work_session_request_invalid_description_length: Correctly raised ValidationError.")

def test_create_work_session_request_extra_fields_forbidden():
    """Test ValidationError when extra fields are provided and extra='forbid'."""
    data = {
        "name": "Valid Session Name",
        "description": "A valid description.",
        "unexpected_field": "some_value"
    }
    with pytest.raises(ValidationError) as excinfo:
        SessionCreate(**data)
    
    assert len(excinfo.value.errors()) == 1
    assert excinfo.value.errors()[0]['type'] == 'extra_forbidden'
    assert excinfo.value.errors()[0]['loc'] == ('unexpected_field',)
    print(f"\n[PASSED] test_create_work_session_request_extra_fields_forbidden: Correctly raised ValidationError for extra field.")
