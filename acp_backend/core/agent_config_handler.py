# acp_backend/core/agent_config_handler.py
import logging
import json
import datetime # Keep this import
import asyncio # Keep this import
from pathlib import Path
from typing import List, Optional, TypeVar
import uuid

# Corrected imports from config.py
from acp_backend.config import AppSettings, app_settings as global_app_settings_instance

# Assuming SessionHandler and its constant are correctly defined and imported
from acp_backend.core.session_handler import SessionHandler
# If SESSION_LOCAL_AGENTS_DIR_NAME is defined in session_handler.py, ensure it's accessible
# For example, if it's a top-level constant in that file:
# from acp_backend.core.session_handler import SESSION_LOCAL_AGENTS_DIR_NAME
# Or if it's part of the class, adjust access.
# For now, assuming it's a constant that can be imported or accessed.
# Let's define it here if it's just a name, to avoid import issues if it's not exported.
SESSION_LOCAL_AGENTS_DIR_NAME = "_agents" # Default name from your previous SessionHandler

from acp_backend.models.agent_models import AgentConfig
# from acp_backend.models.work_session_models import WorkSession # This import was unused

logger = logging.getLogger(__name__)

# Update TypeVar to use the correct settings class name
TSettings = TypeVar('TSettings', bound=AppSettings)

class AgentConfigHandler:
    def __init__(self, 
                 session_handler_instance: SessionHandler, 
                 # settings_override is for testing, main dependency injection won't pass it
                 settings_override: Optional[TSettings] = None): 
        
        # Use the globally imported app_settings if no override is provided
        current_settings_instance = settings_override if settings_override is not None else global_app_settings_instance
        
        self.settings: AppSettings = current_settings_instance # Ensure type hint matches
        self.session_handler: SessionHandler = session_handler_instance
        
        # Use the property from AppSettings for the path
        self.global_configs_base_path: Path = self.settings.GLOBAL_AGENT_CONFIGS_DIR
        
        self._ensure_global_config_directory_exists()
        logger.info(f"AgentConfigHandler initialized. Global configs path: {self.global_configs_base_path}")

    def _ensure_global_config_directory_exists(self):
        try:
            self.global_configs_base_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.critical(f"AgentConfigHandler critical failure: Could not create global config directory {self.global_configs_base_path}: {e}")
            # Consider if this should halt application startup if it's truly critical
            raise RuntimeError(f"AgentConfigHandler critical failure: Could not create global config directory {self.global_configs_base_path}: {e}")

    def _validate_agent_id_format(self, agent_id: str):
        if not agent_id or ".." in agent_id or "/" in agent_id or "\\" in agent_id:
            logger.error(f"Attempted to use invalid agent_id format: '{agent_id}'")
            raise ValueError(f"Invalid agent_id format: '{agent_id}'")

    def _get_global_agent_config_file_path(self, agent_id: str) -> Path:
        self._validate_agent_id_format(agent_id)
        return self.global_configs_base_path / f"{agent_id}.json"

    async def _get_local_agent_configs_base_path(self, session_id_str: str) -> Path:
        # Convert string session_id to UUID for SessionHandler methods
        try:
            session_uuid = uuid.UUID(session_id_str)
        except ValueError:
            logger.error(f"Invalid session_id format for UUID conversion: '{session_id_str}'")
            raise ValueError(f"Invalid session_id format: '{session_id_str}'")

        # Use the public async method from SessionHandler
        # This method also ensures the directory exists.
        local_agents_path = await self.session_handler.get_local_agent_configs_path(session_uuid)
        return local_agents_path

    async def _get_local_agent_config_file_path(self, session_id: str, agent_id: str) -> Path:
        self._validate_agent_id_format(agent_id)
        local_configs_base_path = await self._get_local_agent_configs_base_path(session_id)
        return local_configs_base_path / f"{agent_id}.json"

    async def _read_agent_config_file(self, file_path: Path, agent_id_expected: str) -> Optional[AgentConfig]:
        logger.debug(f"Attempting to read agent config file: {file_path} for agent_id: {agent_id_expected}")
        if not await asyncio.to_thread(file_path.is_file):
            logger.debug(f"Agent config file not found: {file_path}")
            return None
        
        try:
            def _read_file_sync(): # Renamed for clarity
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            data = await asyncio.to_thread(_read_file_sync)
            config = AgentConfig(**data) # Assuming AgentConfig is a Pydantic model
            if config.agent_id != agent_id_expected:
                logger.warning(f"Agent config file '{file_path}' has mismatched agent_id. Expected: {agent_id_expected}, Found: {config.agent_id}. Ignoring.")
                return None
            return config
        except (json.JSONDecodeError, ValueError) as e: # ValueError for Pydantic validation
            logger.error(f"Corrupted or invalid agent config file found at '{file_path}': {e}")
            return None
        except Exception as e: # Catch other potential errors
            logger.error(f"Error reading agent config file '{file_path}': {e}", exc_info=True)
            # Depending on policy, you might want to re-raise certain errors
            return None # Or raise e

    async def _write_agent_config_file(self, file_path: Path, config: AgentConfig):
        logger.debug(f"Attempting to write agent config file: {file_path} for agent_id: {config.agent_id}")
        await asyncio.to_thread(file_path.parent.mkdir, parents=True, exist_ok=True)
        try:
            def _write_file_sync(): # Renamed for clarity
                # Assuming AgentConfig is a Pydantic model
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config.model_dump(mode='json'), f, indent=4)
            await asyncio.to_thread(_write_file_sync)
        except IOError as e:
            logger.error(f"Failed to write agent config to '{file_path}': {e}")
            raise # Re-raise IOError

    async def save_global_agent_config(self, config: AgentConfig):
        file_path = self._get_global_agent_config_file_path(config.agent_id)
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        existing_config = await self.get_global_agent_config(config.agent_id)
        if existing_config:
            # Assuming AgentConfig model has created_at and updated_at fields
            config.created_at = existing_config.created_at 
            config.updated_at = now_iso
        else:
            config.created_at = now_iso 
            config.updated_at = now_iso
        
        await self._write_agent_config_file(file_path, config)
        logger.info(f"Saved global agent config: {config.agent_id}")

    async def get_global_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        file_path = self._get_global_agent_config_file_path(agent_id)
        return await self._read_agent_config_file(file_path, agent_id)

    async def list_global_agent_configs(self) -> List[AgentConfig]:
        configs: List[AgentConfig] = []
        if not await asyncio.to_thread(self.global_configs_base_path.exists):
            return []

        # Ensure globbing is done in a thread if it can be slow on large dirs
        def _glob_files_sync():
            return list(self.global_configs_base_path.glob("*.json"))
            
        file_paths = await asyncio.to_thread(_glob_files_sync)
        for file_path in file_paths:
            agent_id = file_path.stem 
            config = await self._read_agent_config_file(file_path, agent_id)
            if config:
                configs.append(config)
        # Sort by updated_at if the field exists on AgentConfig
        if configs and hasattr(configs[0], 'updated_at') and configs[0].updated_at:
            configs.sort(key=lambda c: c.updated_at, reverse=True) # type: ignore
        elif configs and hasattr(configs[0], 'created_at') and configs[0].created_at:
            configs.sort(key=lambda c: c.created_at, reverse=True) # type: ignore
        return configs

    async def delete_global_agent_config(self, agent_id: str) -> bool:
        file_path = self._get_global_agent_config_file_path(agent_id)
        if not await asyncio.to_thread(file_path.is_file):
            logger.info(f"Global agent config '{agent_id}' not found for deletion.")
            return False # Changed from True to indicate not found was not an error, but deletion didn't occur
        
        try:
            await asyncio.to_thread(file_path.unlink)
            logger.info(f"Deleted global agent config: {agent_id}")
            return True
        except OSError as e:
            logger.error(f"Failed to delete global agent config '{agent_id}': {e}")
            raise 

    async def save_local_agent_config(self, session_id: str, config: AgentConfig):
        # Session existence check should be in SessionHandler or done by caller if critical before this
        # For now, assuming session_id is valid if it reaches here, or path creation will fail.
        # The original code had: session = await self.session_handler.get_session(session_id)
        # This is a good check. Let's assume get_session is an async method in SessionHandler.
        if not await self.session_handler.get_session_metadata(session_id): # Assuming get_session_metadata checks existence
            raise FileNotFoundError(f"Work Session ID '{session_id}' not found.")

        local_configs_base_path = await self._get_local_agent_configs_base_path(session_id)
        file_path = local_configs_base_path / f"{config.agent_id}.json"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        existing_config = await self.get_local_agent_config(session_id, config.agent_id)
        if existing_config:
            config.created_at = existing_config.created_at
            config.updated_at = now_iso
        else:
            config.created_at = now_iso 
            config.updated_at = now_iso
        
        await self._write_agent_config_file(file_path, config)
        logger.info(f"Saved local agent config '{config.agent_id}' for session '{session_id}'.")

    async def get_local_agent_config(self, session_id: str, agent_id: str) -> Optional[AgentConfig]:
        try:
            # Check session existence first
            if not await self.session_handler.get_session_metadata(session_id):
                logger.debug(f"Session '{session_id}' not found when trying to get local agent config '{agent_id}'.")
                return None
            
            file_path = await self._get_local_agent_config_file_path(session_id, agent_id)
            return await self._read_agent_config_file(file_path, agent_id)
        except FileNotFoundError: # This might be raised by _get_local_agent_configs_base_path if session not found
            logger.debug(f"Session path not found for '{session_id}' when getting local agent config.")
            return None
        except ValueError: # From _validate_agent_id_format
            raise 

    async def list_local_agent_configs(self, session_id: str) -> List[AgentConfig]:
        if not await self.session_handler.get_session_metadata(session_id):
            raise FileNotFoundError(f"Work Session ID '{session_id}' not found.")

        local_configs_base_path = await self._get_local_agent_configs_base_path(session_id)
        configs: List[AgentConfig] = []
        if not await asyncio.to_thread(local_configs_base_path.exists):
            return []

        def _glob_files_sync_local():
            return list(local_configs_base_path.glob("*.json"))
            
        file_paths = await asyncio.to_thread(_glob_files_sync_local)
        for file_path in file_paths:
            agent_id = file_path.stem
            config = await self._read_agent_config_file(file_path, agent_id)
            if config:
                configs.append(config)
        
        if configs and hasattr(configs[0], 'updated_at') and configs[0].updated_at:
            configs.sort(key=lambda c: c.updated_at, reverse=True) # type: ignore
        elif configs and hasattr(configs[0], 'created_at') and configs[0].created_at:
            configs.sort(key=lambda c: c.created_at, reverse=True) # type: ignore
        return configs

    async def delete_local_agent_config(self, session_id: str, agent_id: str) -> bool:
        # Convert session_id string to UUID for SessionHandler methods
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            # Log or raise more specific error if session_id format is critical here
            raise FileNotFoundError(f"Work Session ID '{session_id}' is not a valid UUID format.")

        if not await self.session_handler.get_session_metadata(session_uuid):
            raise FileNotFoundError(f"Work Session ID '{session_id}' not found.")

        file_path = await self._get_local_agent_config_file_path(session_id, agent_id) # This still takes string session_id
        if not await asyncio.to_thread(file_path.is_file):
            logger.info(f"Local agent config '{agent_id}' for session '{session_id}' not found for deletion.")
            return False
        
        try:
            await asyncio.to_thread(file_path.unlink)
            logger.info(f"Deleted local agent config '{agent_id}' for session '{session_id}'.")
            return True
        except OSError as e:
            logger.error(f"Failed to delete local agent config '{agent_id}' for session '{session_id}': {e}")
            raise

    async def get_effective_agent_config(self, agent_id: str, session_id: Optional[str] = None) -> Optional[AgentConfig]:
        if session_id:
            try:
                session_uuid = uuid.UUID(session_id) # Convert string to UUID
                if not await self.session_handler.get_session_metadata(session_uuid): # Use UUID object
                    logger.warning(f"Session ID '{session_id}' not found for effective agent config lookup. Falling back to global.")
                else:
                    # get_local_agent_config takes session_id as string, it handles UUID conversion internally if needed by sub-methods
                    local_config = await self.get_local_agent_config(session_id, agent_id)
                    if local_config:
                        logger.debug(f"Resolved agent '{agent_id}' from local session '{session_id}'.")
                        return local_config
            except FileNotFoundError: 
                logger.debug(f"Session folder not found for session '{session_id}' during local agent config lookup, falling back to global.")
            except ValueError: # Catches errors from uuid.UUID(session_id) or from _validate_agent_id_format
                logger.warning(f"Invalid session_id '{session_id}' or agent_id '{agent_id}' provided for effective agent config lookup. Falling back to global.")

        global_config = await self.get_global_agent_config(agent_id)
        if global_config:
            logger.debug(f"Resolved agent '{agent_id}' from global configuration.")
            return global_config
        
        logger.debug(f"Agent config '{agent_id}' not found globally or locally (session: {session_id or 'None'}).")
        return None
