# <PROJECT_ROOT>/tests/unit/models/test_agent_models.py
import pytest
from pydantic import ValidationError
import datetime

from acp_backend.models.agent_models import AgentConfig, AgentToolConfig, RunAgentRequest, AgentRunStatus, AgentOutputChunk

# --- AgentToolConfig Tests ---
def test_agent_tool_config_valid():
    tool_config = AgentToolConfig(tool_id="web_search", params={"api_key_env": "SERPER_API_KEY"})
    assert tool_config.tool_id == "web_search"
    assert tool_config.params == {"api_key_env": "SERPER_API_KEY"}
    print(f"\n[PASSED] test_agent_tool_config_valid")

def test_agent_tool_config_missing_tool_id():
    with pytest.raises(ValidationError) as excinfo:
        AgentToolConfig(params={})
    assert "tool_id" in str(excinfo.value).lower() 
    print(f"\n[PASSED] test_agent_tool_config_missing_tool_id")

# --- AgentConfig Tests ---
def test_agent_config_valid_minimal():
    """Test AgentConfig with minimal required fields."""
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat() # Capture 'now' before model instantiation
    data = {
        "agent_id": "test-agent-001",
        "name": "Minimal Agent",
        "llm_model_id": "test-llm-v1",
    }
    config = AgentConfig(**data)
    assert config.agent_id == data["agent_id"]
    assert config.name == data["name"]
    assert config.llm_model_id == data["llm_model_id"]
    assert config.agent_type == "CodeAgent" 
    assert config.llm_config_overrides == {} 
    assert config.tools == [] 
    assert config.additional_authorized_imports == [] 
    assert isinstance(config.created_at, str)
    assert isinstance(config.updated_at, str)
    
    created_dt = datetime.datetime.fromisoformat(config.created_at.replace("Z", "+00:00"))
    now_dt = datetime.datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
    assert abs((created_dt - now_dt).total_seconds()) < 5, f"Timestamp created_at {config.created_at} is too far from {now_iso}"
    print(f"\n[PASSED] test_agent_config_valid_minimal")

def test_agent_config_valid_all_fields():
    """Test AgentConfig with all fields populated."""
    # Generate fixed timestamps for predictable test data
    created_ts = datetime.datetime(2023, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc).isoformat()
    updated_ts = datetime.datetime(2023, 1, 1, 10, 5, 0, tzinfo=datetime.timezone.utc).isoformat()
    data = {
        "agent_id": "test-agent-002",
        "name": "Full Agent",
        "description": "A comprehensive agent.",
        "agent_type": "ToolCallingAgent",
        "system_prompt": "You are a helpful assistant with tools.",
        "llm_model_id": "gpt-4",
        "llm_config_overrides": {"temperature": 0.8, "max_tokens": 1000},
        "tools": ["web_search", "calculator"],
        "max_steps": 20,
        "additional_authorized_imports": ["math"],
        "created_at": created_ts, # Use fixed timestamp
        "updated_at": updated_ts  # Use fixed timestamp
    }
    config = AgentConfig(**data)
    for key, value in data.items():
        assert getattr(config, key) == value
    print(f"\n[PASSED] test_agent_config_valid_all_fields")

def test_agent_config_missing_required_fields():
    """Test AgentConfig for missing required fields (agent_id, name, llm_model_id)."""
    with pytest.raises(ValidationError) as excinfo:
        AgentConfig(name="Incomplete Agent", llm_model_id="some-llm") # Missing agent_id
    assert "agent_id" in str(excinfo.value).lower()

    with pytest.raises(ValidationError) as excinfo:
        AgentConfig(agent_id="incomplete-001", llm_model_id="some-llm") # Missing name
    assert "name" in str(excinfo.value).lower()

    with pytest.raises(ValidationError) as excinfo:
        AgentConfig(agent_id="incomplete-002", name="Agent No LLM") # Missing llm_model_id
    assert "llm_model_id" in str(excinfo.value).lower()
    print(f"\n[PASSED] test_agent_config_missing_required_fields")


@pytest.mark.parametrize("invalid_value, field_name, constraint_key_from_pydantic_type", [
    ("", "name", "string_too_short"),
    (0, "max_steps", "greater_than"),
])
def test_agent_config_invalid_constraints(invalid_value, field_name, constraint_key_from_pydantic_type):
    """Test AgentConfig field constraints."""
    valid_data = {
        "agent_id": "constraint-test",
        "name": "Constraint Agent",
        "llm_model_id": "llm-for-constraints",
    }
    if field_name != "max_steps":
        valid_data["max_steps"] = 10 

    invalid_data = valid_data.copy()
    invalid_data[field_name] = invalid_value
    
    with pytest.raises(ValidationError) as excinfo:
        AgentConfig(**invalid_data)
    
    print(f"\nDEBUG: For {field_name}='{invalid_value}', errors are: {excinfo.value.errors()}")

    error_found = False
    for error in excinfo.value.errors():
        if error.get('loc') and field_name == error['loc'][0] and constraint_key_from_pydantic_type.lower() == error.get('type','').lower():
            error_found = True
            break
    assert error_found, f"Expected validation error for {field_name} with type '{constraint_key_from_pydantic_type}'. Actual errors: {excinfo.value.errors()}"
    print(f"\n[PASSED] test_agent_config_invalid_constraints for {field_name}='{invalid_value}'")

def test_agent_config_extra_fields_forbidden():
    data = {
        "agent_id": "test-agent-extra", "name": "Extra Agent", "llm_model_id": "test-llm",
        "unknown_field": "should_fail"
    }
    with pytest.raises(ValidationError) as excinfo:
        AgentConfig(**data)
    assert excinfo.value.errors()[0]['type'] == 'extra_forbidden'
    print(f"\n[PASSED] test_agent_config_extra_fields_forbidden")

# --- RunAgentRequest Tests ---
def test_run_agent_request_valid():
    req = RunAgentRequest(agent_id="agent-001", input_prompt="Hello agent!")
    assert req.agent_id == "agent-001"
    assert req.input_prompt == "Hello agent!"
    print(f"\n[PASSED] test_run_agent_request_valid")

def test_run_agent_request_invalid_input_prompt():
    with pytest.raises(ValidationError) as excinfo:
        RunAgentRequest(agent_id="agent-001", input_prompt="") # Empty prompt
    assert "input_prompt" in str(excinfo.value).lower()
    assert "string_too_short" in excinfo.value.errors()[0]['type'].lower()
    print(f"\n[PASSED] test_run_agent_request_invalid_input_prompt")

# --- AgentRunStatus Tests ---
def test_agent_run_status_minimal():
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    status_obj = AgentRunStatus(run_id="run-123", agent_id="agent-abc", status="starting")
    assert status_obj.run_id == "run-123"
    assert status_obj.status == "starting"
    assert isinstance(status_obj.start_time, str)
    
    start_dt = datetime.datetime.fromisoformat(status_obj.start_time.replace("Z", "+00:00"))
    now_dt = datetime.datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
    assert abs((start_dt - now_dt).total_seconds()) < 5, f"Timestamp start_time {status_obj.start_time} is too far from {now_iso}"
    print(f"\n[PASSED] test_agent_run_status_minimal")

# --- AgentOutputChunk Tests ---
def test_agent_output_chunk_valid():
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    chunk = AgentOutputChunk(run_id="run-123", type="log", data="Processing step 1")
    assert chunk.type == "log"
    assert chunk.data == "Processing step 1"
    assert isinstance(chunk.timestamp, str)
    
    chunk_dt = datetime.datetime.fromisoformat(chunk.timestamp.replace("Z", "+00:00"))
    now_dt = datetime.datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
    assert abs((chunk_dt - now_dt).total_seconds()) < 5, f"Timestamp {chunk.timestamp} is too far from {now_iso}"
    print(f"\n[PASSED] test_agent_output_chunk_valid")
