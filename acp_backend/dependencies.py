# acp_backend/dependencies.py
import logging
from functools import lru_cache # Keep for settings
from typing import Optional

from fastapi import HTTPException, status, Depends

from acp_backend.config import settings, Settings
from acp_backend.core.session_handler import SessionHandler
from acp_backend.core.llm_manager import LLMManager
from acp_backend.core.agent_config_handler import AgentConfigHandler
from acp_backend.core.fs_manager import FileSystemManager
from acp_backend.core.agent_executor import AgentExecutor

logger = logging.getLogger(__name__)

@lru_cache()
def get_settings_dependency() -> Settings:
    return settings

def get_session_handler_dependency() -> SessionHandler:
    logger.debug("Providing SessionHandler instance")
    return SessionHandler()

def get_llm_manager_dependency() -> Optional[LLMManager]:
    logger.debug("Attempting to provide LLMManager instance")
    if not settings.ENABLE_LLM_MODULE:
        logger.info("LLM module disabled, providing None for LLMManager.")
        return None
    try:
        return LLMManager()
    except ValueError as e:
        logger.critical(f"Failed to initialize LLMManager in dependency provider: {e}")
        return None

def get_agent_config_handler_dependency(
    # Explicitly type hint what FastAPI will inject here
    session_handler_instance: SessionHandler = Depends(get_session_handler_dependency)
) -> AgentConfigHandler:
    logger.debug(f"Providing AgentConfigHandler instance with SessionHandler: {type(session_handler_instance)}")
    return AgentConfigHandler(
        session_handler_instance=session_handler_instance,
        settings_override=settings # AgentConfigHandler now uses the global settings by default
                                   # but for tests, the test_agent_config_handler fixture
                                   # will pass temp_settings_for_test via its constructor.
                                   # The override in conftest.py for get_agent_config_handler_dependency
                                   # will return this test_agent_config_handler.
    )

def get_fs_manager_dependency(
    session_handler_instance: SessionHandler = Depends(get_session_handler_dependency)
) -> FileSystemManager:
    logger.debug(f"Providing FileSystemManager instance with SessionHandler: {type(session_handler_instance)}")
    # FileSystemManager also needs settings if it uses global settings for paths.
    # Assuming it primarily relies on session_handler for paths.
    # If not, it would need a settings_override parameter like AgentConfigHandler.
    return FileSystemManager(session_handler_instance=session_handler_instance)

def get_agent_executor_dependency(
    # Explicitly type hint what FastAPI will inject here
    resolved_agent_config_handler: AgentConfigHandler = Depends(get_agent_config_handler_dependency),
    resolved_llm_manager: Optional[LLMManager] = Depends(get_llm_manager_dependency)
) -> AgentExecutor:
    logger.debug(f"Providing AgentExecutor. AgentConfigHandler type: {type(resolved_agent_config_handler)}, LLMManager type: {type(resolved_llm_manager)}")
    return AgentExecutor(
        agent_config_handler_instance=resolved_agent_config_handler,
        llm_manager_instance=resolved_llm_manager
    )
