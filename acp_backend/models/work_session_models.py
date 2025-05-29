# acp_backend/models/work_session_models.py
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field, field_validator, ConfigDict

# --- Base Model for common fields ---
class SessionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the work session")
    description: Optional[str] = Field(None, max_length=500, description="Optional description for the session")
    # Example of how custom UI settings might be structured if you persist them
    # custom_ui_settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom UI settings for this session")

# --- Model for creating a new session ---
# This is what SessionHandler expects to be named SessionCreate
class SessionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the work session")
    description: Optional[str] = Field(None, max_length=500, description="Optional description for the session")
    # custom_ui_settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom UI settings for the session")

    model_config = ConfigDict(extra='forbid')

# --- Model for updating an existing session ---
# Fields are optional because it's a PATCH-like update
# This is what SessionHandler expects to be named SessionUpdate
class SessionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    # custom_ui_settings: Optional[Dict[str, Any]] = Field(None, description="Custom UI settings to update or add")
    # You generally wouldn't update id, created_at, or updated_at directly via this model

# --- Model for representing stored session metadata (e.g., in session_manifest.json) ---
# This is what SessionHandler expects to be named SessionMetadata
class SessionMetadata(SessionBase):
    id: uuid.UUID = Field(..., description="Unique identifier for the session")
    created_at: datetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc), description="Timestamp of session creation")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc), description="Timestamp of last session update")
    
    # Ensure timestamps are timezone-aware (UTC)
    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def ensure_timezone(cls, v):
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=datetime.timezone.utc)
        return v

# --- Model for API responses when listing sessions ---
# Often, this might be the same as SessionMetadata or a subset
class SessionResponse(SessionMetadata):
    pass # Inherits all fields from SessionMetadata

# You might also have a model for a list of sessions if your API returns it structured
# class SessionListResponse(BaseModel):
#     sessions: List[SessionResponse]
#     total: int
