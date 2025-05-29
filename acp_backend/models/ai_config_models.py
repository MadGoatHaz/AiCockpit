"""
ACP Backend - Pydantic Models for AI Session Configuration
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class AIModelSessionConfig(BaseModel):
    selected_model_id: Optional[str] = Field(None, description="The ID of the AI model selected for this session")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="The temperature setting for the AI model in this session")
    # We can add other model-specific parameters here later, perhaps in a dict
    # custom_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "selected_model_id": "gemma2-latest",
                    "temperature": 0.7
                }
            ]
        }
    } 