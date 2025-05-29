# acp_backend/core/__init__.py
import logging

# Only import the classes themselves for easier access from acp_backend.core
from .session_handler import SessionHandler
from .llm_manager import LLMManager
from .agent_config_handler import AgentConfigHandler
from .fs_manager import FileSystemManager
from .agent_executor import AgentExecutor

# If you need to access app_settings directly within the core package (outside of DI),
# then this import would be:
# from acp_backend.config import app_settings
# However, it's generally better for core components to receive settings via their
# __init__ methods when instantiated by the dependency injector, rather than
# relying on a global import here.

logger = logging.getLogger(__name__)
logger.debug("acp_backend.core package initialized. Classes are available for import.")

# The __all__ list controls what 'from acp_backend.core import *' imports.
# It's good practice to define it.
__all__ = [
    "SessionHandler",
    "LLMManager",
    "AgentConfigHandler",
    "FileSystemManager",
    "AgentExecutor",
]

# DO NOT INSTANTIATE SINGLETONS HERE.
# Singleton instantiation and provision should be handled by
# acp_backend.dependencies.py for FastAPI's dependency injection.
# This ensures a single source of truth for these instances and facilitates testing/mocking.

# Removed original singleton instantiation block:
# session_handler = SessionHandler()
# llm_manager = None
# if settings.ENABLE_LLM_MODULE: # This used the old 'settings'
#     try:
#         llm_manager = LLMManager()
#     except ValueError as e:
#         logger.critical(f"Core __init__: Failed to initialize LLMManager: {e}. LLM functionalities may be unavailable.", exc_info=True)
# else:
#     logger.info("Core __init__: LLM module disabled, LLMManager not initialized.")
# agent_config_handler = AgentConfigHandler(session_handler_instance=session_handler)
# fs_manager = FileSystemManager(session_handler_instance=session_handler)
# agent_executor = AgentExecutor(
#     agent_config_handler_instance=agent_config_handler,
#     llm_manager_instance=llm_manager
# )
