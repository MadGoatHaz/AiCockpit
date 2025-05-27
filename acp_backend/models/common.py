# acp_backend/models/common.py
from pydantic import BaseModel, Field, ConfigDict 
from typing import Optional, Dict, Any, Literal
import datetime

class StatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid") 

    status: str
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class PingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid") 

    ping: Literal["pong"] = Field("pong", description="Always returns 'pong'.")
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(), description="ISO timestamp of when the ping was processed.")
