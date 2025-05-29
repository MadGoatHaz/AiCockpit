# acp_backend/dependencies.py
import logging
from typing import Optional, Annotated

from fastapi import Depends

from acp_backend.config import app_settings, AppSettings

from acp_backend.core.session_handler import SessionHandler
from acp_backend.core.llm_manager import LLMManager
from acp_backend.core.agent_config_handler import AgentConfigHandler
from acp_backend.core.fs_manager import FileSystemManager
from acp_backend.core.agent_executor import AgentExecutor

logger = logging.getLogger(__name__)

# --- Singleton instances ---
_session_handler_instance: Optional[SessionHandler] = None
_llm_manager_instance: Optional[LLMManager] = None
_agent_config_handler_instance: Optional[AgentConfigHandler] = None
_fs_manager_instance: Optional[FileSystemManager] = None
_agent_executor_instance: Optional[AgentExecutor] = None


def get_app_settings() -> AppSettings: # Name is fine
    """Dependency to get the application settings instance."""
    return app_settings


def get_session_handler( # Renamed from get_session_handler_dependency
    current_app_settings: Annotated[AppSettings, Depends(get_app_settings)]
) -> SessionHandler:
    """Dependency to get the SessionHandler singleton instance."""
    global _session_handler_instance
    if _session_handler_instance is None:
        logger.info("Initializing SessionHandler singleton.")
        _session_handler_instance = SessionHandler(
            base_dir=str(current_app_settings.WORK_SESSIONS_DIR)
        )
    logger.debug("Providing SessionHandler instance.")
    return _session_handler_instance


def get_llm_manager( # Renamed from get_llm_manager_dependency
    current_app_settings: Annotated[AppSettings, Depends(get_app_settings)]
) -> Optional[LLMManager]:
    """Dependency to get the LLMManager singleton instance."""
    global _llm_manager_instance

    if not current_app_settings.ENABLE_LLM_SERVICE_MODULE:
        logger.info("LLM Service module disabled by configuration, providing None for LLMManager.")
        return None

    if _llm_manager_instance is None:
        logger.info("Initializing LLMManager singleton.")
        try:
            _llm_manager_instance = LLMManager(
                models_dir=str(current_app_settings.MODELS_DIR),
                default_backend_type=current_app_settings.LLM_BACKEND_TYPE
            )
        except Exception as e:
            logger.critical(f"Failed to initialize LLMManager in dependency provider: {e}", exc_info=True)
            return None
            
    logger.debug("Providing LLMManager instance.")
    return _llm_manager_instance


def get_agent_config_handler( # Renamed from get_agent_config_handler_dependency
    current_app_settings: Annotated[AppSettings, Depends(get_app_settings)]
) -> AgentConfigHandler:
    """Dependency to get the AgentConfigHandler singleton instance."""
    global _agent_config_handler_instance
    if _agent_config_handler_instance is None:
        logger.info("Initializing AgentConfigHandler singleton.")
        _agent_config_handler_instance = AgentConfigHandler(
            global_configs_path=str(current_app_settings.GLOBAL_AGENT_CONFIGS_DIR)
            # The SessionHandler dependency for AgentConfigHandler was removed from its constructor
            # in message #38, File 1, as it seemed to primarily need settings for its path.
            # If AgentConfigHandler's __init__ *does* require session_handler_instance,
            # you'd add:
            # session_handler: Annotated[SessionHandler, Depends(get_session_handler)]
            # and pass session_handler_instance=session_handler to the constructor.
            # The version from message #38 did not require it.
        )
    logger.debug("Providing AgentConfigHandler instance.")
    return _agent_config_handler_instance


def get_fs_manager( # Renamed from get_fs_manager_dependency
    session_handler_instance: Annotated[SessionHandler, Depends(get_session_handler)] # Uses renamed get_session_handler
) -> FileSystemManager:
    """Dependency to get the FileSystemManager singleton instance."""
    global _fs_manager_instance
    if _fs_manager_instance is None:
        logger.info("Initializing FileSystemManager singleton.")
        _fs_manager_instance = FileSystemManager(session_handler_instance=session_handler_instance)
    logger.debug("Providing FileSystemManager instance.")
    return _fs_manager_instance


def get_agent_executor( # Renamed from get_agent_executor_dependency
    current_app_settings: Annotated[AppSettings, Depends(get_app_settings)],
    resolved_agent_config_handler: Annotated[AgentConfigHandler, Depends(get_agent_config_handler)], # Uses renamed get_agent_config_handler
    resolved_llm_manager: Annotated[Optional[LLMManager], Depends(get_llm_manager)] # Uses renamed get_llm_manager
) -> Optional[AgentExecutor]:
    """Dependency to get the AgentExecutor singleton instance."""
    global _agent_executor_instance

    if not current_app_settings.ENABLE_AGENTS_MODULE:
        logger.info("Agents module disabled by configuration, providing None for AgentExecutor.")
        return None

    if current_app_settings.ENABLE_LLM_SERVICE_MODULE and resolved_llm_manager is None:
        logger.warning("LLMManager is None; AgentExecutor may not function as expected or will be None.")
        return None 
        
    if _agent_executor_instance is None:
        logger.info("Initializing AgentExecutor singleton.")
        _agent_executor_instance = AgentExecutor(
            agent_config_handler_instance=resolved_agent_config_handler,
            llm_manager_instance=resolved_llm_manager
        )
    logger.debug("Providing AgentExecutor instance.")
    return _agent_executor_instance
