# acp_backend/config.py
import os
import sys
from pathlib import Path
from typing import Optional, List

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "AiCockpit Backend"
    APP_VERSION: str = "0.1.0-alpha"
    APP_PORT: int = 8000
    DEBUG_MODE: bool = False
    
    ENABLE_LLM_MODULE: bool = True
    ENABLE_AGENT_MODULE: bool = True
    ENABLE_WORK_SESSION_MODULE: bool = True
    ENABLE_WORK_BOARD_MODULE: bool = True
    ENABLE_SYSTEM_MODULE: bool = True

    ACP_BASE_DIR: Path = Path.home() / ".acp"

    MODELS_DIR: Path = ACP_BASE_DIR / "llm_models"
    WORK_SESSIONS_DIR: Path = ACP_BASE_DIR / "work_sessions"
    LOG_DIR: Path = ACP_BASE_DIR / "logs"
    TEMP_DIR: Path = ACP_BASE_DIR / "temp"

    GLOBAL_AGENT_CONFIGS_DIR_NAME: str = "_agent_configs"

    LLM_BACKEND_TYPE: str = "llama_cpp"
    LLAMA_CPP_MODEL_PATH: Optional[str] = Field(None, description="Default GGUF model path or ID if no model is specified in API load requests.")
    LLAMA_CPP_N_GPU_LAYERS: int = 0
    LLAMA_CPP_N_CTX: int = 2048
    LLAMA_CPP_N_BATCH: int = 512
    LLAMA_CPP_CHAT_FORMAT: str = "llama-2"
    LLAMA_CPP_VERBOSE: bool = False

    SMOLAGENTS_DEFAULT_MODEL: Optional[str] = Field(None, description="Default LLM model ID for smol-ai-agents if not specified in agent config.")
    SERPER_API_KEY: Optional[str] = Field(None, description="API Key for Serper.dev web search tool.")

    model_config = SettingsConfigDict(
        env_file=os.path.join(PROJECT_ROOT, ".env"), 
        env_file_encoding='utf-8',
        extra='ignore'
    )

    def get_global_agent_configs_path(self) -> Path:
        return self.WORK_SESSIONS_DIR / self.GLOBAL_AGENT_CONFIGS_DIR_NAME

settings = Settings()

# Directory creation logic for initial setup (can be moved to main.py lifespan)
try:
    settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    settings.WORK_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    settings.get_global_agent_configs_path().mkdir(parents=True, exist_ok=True)
except OSError as e:
    print(f"Warning: Could not create one or more default ACP directories: {e}", file=sys.stderr)
