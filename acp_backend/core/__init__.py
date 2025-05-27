# acp_backend/core/__init__.py
import logging
from pathlib import Path 

# Import Classes first
from acp_backend.core.session_handler import SessionHandler
from acp_backend.core.llm_manager import LLMManager
from acp_backend.core.agent_config_handler import AgentConfigHandler
from acp_backend.core.fs_manager import FileSystemManager 
from acp_backend.core.agent_executor import AgentExecutor

# Import settings for conditional LLMManager initialization
from acp_backend.config import settings 

logger = logging.getLogger(__name__)

# Instantiate singletons in a defined order
# 1. Handlers with no internal 'core' dependencies (other than settings)
session_handler = SessionHandler()

llm_manager = None
if settings.ENABLE_LLM_MODULE:
    try:
        llm_manager = LLMManager()
    except ValueError as e: 
        logger.critical(f"Core __init__: Failed to initialize LLMManager: {e}. LLM functionalities may be unavailable.", exc_info=True)
        # llm_manager remains None
else:
    logger.info("Core __init__: LLM module disabled, LLMManager not initialized.")

# 2. Handlers that depend on previously created handlers
agent_config_handler = AgentConfigHandler(session_handler_instance=session_handler) 
fs_manager = FileSystemManager(session_handler_instance=session_handler) 
agent_executor = AgentExecutor(
    agent_config_handler_instance=agent_config_handler,
    llm_manager_instance=llm_manager # Pass llm_manager (which could be None)
)

__all__ = [
    "fs_manager", "session_handler", "llm_manager", 
    "agent_config_handler", "agent_executor",
    "FileSystemManager", "SessionHandler", "LLMManager", 
    "AgentConfigHandler", "AgentExecutor",  
]
