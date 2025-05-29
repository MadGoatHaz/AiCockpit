# acp_backend/config.py
import logging
import os
from pathlib import Path
from typing import Literal

from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# --- Logging Setup ---
# It's often good to have setup_logging here if config.py is imported early
# or keep it as a separate function called from main.py after settings are loaded.
# For now, let's define it here as per the import in main.py
def setup_logging(log_level_str: str = "INFO"):
    """Configures application-wide logging."""
    numeric_level = getattr(logging, log_level_str.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level_str}")

    # Ensure log directory exists
    log_dir = AppSettings().LOG_DIR # Get LOG_DIR from default AppSettings instance
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "acp_backend.log"

    # Basic configuration
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Log to console
            logging.FileHandler(log_file),  # Log to file
        ],
    )
    # You can add more specific logger configurations here if needed
    # For example, set different levels for different libraries:
    # logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Level: {log_level_str}. Log file: {log_file}")


# --- Application Settings ---
class AppSettings(BaseSettings):
    APP_VERSION: str = "0.2.0-alpha"
    DEBUG: bool = False
    PORT: int = Field(default=8000, description="Port to run the backend server on")

    # Core Directories
    # It's good practice to define a base directory and derive others from it.
    ACP_BASE_DIR: Path = Field(default_factory=lambda: Path.home() / ".acp", description="Base directory for AiCockpit data")
    WORK_SESSIONS_DIR_NAME: str = "work_sessions"
    GLOBAL_AGENT_CONFIGS_DIR_NAME: str = "_agent_configs" # Relative to WORK_SESSIONS_DIR
    MODELS_DIR_NAME: str = "llm_models"
    LOG_DIR_NAME: str = "logs"
    TEMP_DIR_NAME: str = "temp"

    # Derived Paths (these will be properties, not direct env vars)
    @property
    def WORK_SESSIONS_DIR(self) -> Path:
        return self.ACP_BASE_DIR / self.WORK_SESSIONS_DIR_NAME

    @property
    def GLOBAL_AGENT_CONFIGS_DIR(self) -> Path:
        # As per your doc, this is under WORK_SESSIONS_DIR
        return self.WORK_SESSIONS_DIR / self.GLOBAL_AGENT_CONFIGS_DIR_NAME

    @property
    def MODELS_DIR(self) -> Path:
        return self.ACP_BASE_DIR / self.MODELS_DIR_NAME
    
    @property
    def LOG_DIR(self) -> Path:
        return self.ACP_BASE_DIR / self.LOG_DIR_NAME

    @property
    def TEMP_DIR(self) -> Path:
        return self.ACP_BASE_DIR / self.TEMP_DIR_NAME

    # Module Enablement Flags
    ENABLE_SYSTEM_MODULE: bool = True
    ENABLE_LLM_SERVICE_MODULE: bool = True
    ENABLE_AGENTS_MODULE: bool = True
    ENABLE_WORK_SESSIONS_MODULE: bool = True
    ENABLE_WORK_BOARD_MODULE: bool = True
    ENABLE_WORKSPACE_FILES_MODULE: bool = True
    ENABLE_TERMINAL_SERVICE_MODULE: bool = True

    # LLM Settings (example, align with your actual needs)
    LLM_BACKEND_TYPE: Literal["llama_cpp", "pie", "mock"] = "llama_cpp"
    # Add specific settings for llama_cpp, pie etc. if needed
    # e.g., LLAMA_CPP_MODEL_PATH: Optional[str] = None (or handled by LLMManager)

    # Agent Settings
    # e.g., SMOLAGENTS_CONFIG_PATH: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"

    # Model configuration
    DEFAULT_MODEL_ID: str = "gemma2-latest"
    DEFAULT_TEMPERATURE: float = 0.7

    # Terminal configuration
    DEFAULT_SHELL_COMMAND: str = "/bin/bash" # Default shell for PTY

    # This validator ensures base directories are created when settings are loaded.
    @field_validator("ACP_BASE_DIR", mode="after")
    @classmethod
    def create_base_directories(cls, value: Path, info) -> Path:
        # We need to access other properties, so we use the values from the info object
        # This is a bit of a workaround as properties are not available yet during this validation.
        # A cleaner way might be a separate function called after app_settings is instantiated.
        # However, for simplicity and to match the "create on import" idea:
        
        # Create base directory first
        value.mkdir(parents=True, exist_ok=True)

        # Create subdirectories using default names if not overridden by env vars
        # Note: This assumes default names. If WORK_SESSIONS_DIR_NAME etc. can be set by env,
        # this logic might need to be in a model_post_init or called explicitly.
        # For now, let's assume these names are fixed relative to ACP_BASE_DIR.
        
        # (value / "work_sessions").mkdir(parents=True, exist_ok=True)
        # (value / "work_sessions" / "_agent_configs").mkdir(parents=True, exist_ok=True) # Handled by SessionHandler/AgentConfigHandler logic usually
        # (value / "llm_models").mkdir(parents=True, exist_ok=True)
        # (value / "logs").mkdir(parents=True, exist_ok=True)
        # (value / "temp").mkdir(parents=True, exist_ok=True)
        # The actual creation of subdirs like WORK_SESSIONS_DIR, MODELS_DIR, LOG_DIR, TEMP_DIR
        # is better handled by their respective managers/handlers or explicitly on app startup
        # after app_settings is fully loaded, to use the derived @property paths.
        # The Handoff doc says: "It also defines and creates necessary base directories ... upon import."
        # This is tricky with Pydantic v2 properties. Let's ensure ACP_BASE_DIR is made.
        # The individual handlers (SessionHandler, LLMManager) should create their specific subdirs.
        return value
    
    # model_post_init is a good place for logic after all fields are loaded
    # def model_post_init(self, __context):
    #     self.WORK_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    #     self.GLOBAL_AGENT_CONFIGS_DIR.mkdir(parents=True, exist_ok=True) # Ensure parent WORK_SESSIONS_DIR exists
    #     self.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    #     self.LOG_DIR.mkdir(parents=True, exist_ok=True)
    #     self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    #     logger.info("Base directories ensured by AppSettings model_post_init.")


    model_config = SettingsConfigDict(
        env_file=".env",                # Load .env file
        env_file_encoding='utf-8',
        extra='ignore',                 # Ignore extra fields from environment
        # case_sensitive=False,         # If your env vars might have different casing
    )

# Instantiate the settings object to be imported by other modules
# This is the line that was likely causing the ImportError if missing or misnamed.
app_settings = AppSettings()

# Call setup_logging after app_settings is available so it can use LOG_DIR and LOG_LEVEL
# Or, main.py can call setup_logging(app_settings.LOG_LEVEL) after importing app_settings.
# To avoid circular dependency if setup_logging needs app_settings, and app_settings needs setup_logging (it doesn't here).
# Let's assume main.py will call setup_logging after importing app_settings.
# For now, to match the import in main.py, we keep setup_logging defined here.
# If main.py calls setup_logging(), it should pass app_settings.LOG_LEVEL and app_settings.LOG_DIR.
# The current setup_logging in main.py doesn't take args, so it implies config.py's setup_logging is self-sufficient
# or uses a default AppSettings() instance as I've modified it to do.
