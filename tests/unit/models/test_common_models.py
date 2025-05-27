import pytest
from pydantic import ValidationError
import datetime
from typing import Literal # For PingResponse.ping

from acp_backend.models.common import StatusResponse, PingResponse

# --- StatusResponse Tests ---
def test_status_response_valid_ok():
    data = {"status": "ok", "message": "Success!", "details": {"code": 123}}
    response = StatusResponse(**data)
    assert response.status == "ok"
    assert response.message == "Success!"
    assert response.details == {"code": 123}
    print(f"\n[PASSED] test_status_response_valid_ok")

def test_status_response_minimal():
    data = {"status": "error"}
    response = StatusResponse(**data)
    assert response.status == "error"
    assert response.message is None
    assert response.details is None
    print(f"\n[PASSED] test_status_response_minimal")

def test_status_response_missing_status():
    with pytest.raises(ValidationError) as excinfo:
        StatusResponse(message="A message without status")
    assert "status" in str(excinfo.value).lower()
    assert excinfo.value.errors()[0]['type'] == 'missing'
    print(f"\n[PASSED] test_status_response_missing_status")

def test_status_response_extra_fields_forbidden():
    data = {"status": "ok", "unexpected": "value"}
    with pytest.raises(ValidationError) as excinfo:
        StatusResponse(**data)
    assert excinfo.value.errors()[0]['type'] == 'extra_forbidden'
    print(f"\n[PASSED] test_status_response_extra_fields_forbidden")


# --- PingResponse Tests ---
def test_ping_response_defaults():
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    response = PingResponse() # Uses default values
    assert response.ping == "pong"
    assert isinstance(response.timestamp, str)
    
    response_dt = datetime.datetime.fromisoformat(response.timestamp.replace("Z", "+00:00"))
    now_dt = datetime.datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
    assert abs((response_dt - now_dt).total_seconds()) < 5, f"Timestamp {response.timestamp} is too far from {now_iso}"
    print(f"\n[PASSED] test_ping_response_defaults")

def test_ping_response_override_timestamp():
    """Test providing a timestamp overrides the default_factory."""
    fixed_ts = "2023-01-01T00:00:00+00:00"
    response = PingResponse(timestamp=fixed_ts)
    assert response.ping == "pong"
    assert response.timestamp == fixed_ts
    print(f"\n[PASSED] test_ping_response_override_timestamp")


def test_ping_response_invalid_ping_value():
    # This test relies on PingResponse.ping being Literal["pong"]
    with pytest.raises(ValidationError) as excinfo:
        PingResponse(ping="not-pong") # type: ignore 
    
    assert len(excinfo.value.errors()) == 1
    assert excinfo.value.errors()[0]['type'] == 'literal_error'
    print(f"\n[PASSED] test_ping_response_invalid_ping_value")


def test_ping_response_extra_fields_forbidden():
    # Ensure timestamp is a valid ISO string for this test
    valid_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    data = {"ping": "pong", "timestamp": valid_timestamp, "extra": "field"}
    with pytest.raises(ValidationError) as excinfo:
        PingResponse(**data)
    assert excinfo.value.errors()[0]['type'] == 'extra_forbidden'
    print(f"\n[PASSED] test_ping_response_extra_fields_forbidden")
