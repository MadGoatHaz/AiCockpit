from pydantic import BaseModel, Field, ConfigDict # Import ConfigDict
from typing import Optional # List, Dict, Any, uuid removed
import datetime 

class WorkSession(BaseModel):
    model_config = ConfigDict(extra="forbid") # Updated

    session_id: str = Field(..., description="Unique identifier for the work session.")
    name: str = Field(..., min_length=1, max_length=100, description="User-defined name for the session.")
    description: Optional[str] = Field(None, max_length=500, description="Brief description of the session's purpose or content.")
    created_at: str = Field(..., description="ISO timestamp of when the session was created.")
    last_accessed: str = Field(..., description="ISO timestamp of when the session was last accessed or modified.")

class CreateWorkSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid") # Updated

    name: str = Field(..., min_length=1, max_length=100, description="Name for the new session.")
    description: Optional[str] = Field(None, max_length=500, description="Optional description for the new session.")

class UpdateWorkSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid") # Updated

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="New name for the session. Must not be empty if provided.")
    description: Optional[str] = Field(None, max_length=500, description="New description for the session. Can be empty string to clear.")
