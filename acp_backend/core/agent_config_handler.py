# acp_backend/core/agent_config_handler.py
import logging
import json
import datetime
import asyncio
from pathlib import Path
from typing import List, Optional, TypeVar

from acp_backend.config import Settings as SettingsClass
from acp_backend.config import settings as global_settings_instance 

from acp_backend.core.session_handler import SessionHandler, LOCAL_AGENTS_DIR_NAME as SESSION_LOCAL_AGENTS_DIR_NAME 

from acp_backend.models.agent_models import AgentConfig
from acp_backend.models.work_session_models import WorkSession 

logger = logging.getLogger(__name__)

TSettings = TypeVar('TSettings', bound=SettingsClass)

class AgentConfigHandler:
    def __init__(self, session_handler_instance: SessionHandler, settings_override: Optional[TSettings] = None):
        current_settings = settings_override if settings_override else global_settings_instance
        
        self.settings = current_settings 
        self.session_handler = session_handler_instance
        self.global_configs_base_path = self.settings.get_global_agent_configs_path()
        
        # DEBUG PRINT REMOVED
        # print(f"DEBUG_AGENT_CONFIG_HANDLER_INIT: Initializing AgentConfigHandler. global_configs_base_path = {self.global_configs_base_path}, ID of settings object used: {id(self.settings)}")

        self._ensure_global_config_directory_exists()
        logger.info(f"AgentConfigHandler initialized. Global configs path: {self.global_configs_base_path}")

    def _ensure_global_config_directory_exists(self):
        try:
            self.global_configs_base_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.critical(f"AgentConfigHandler critical failure: Could not create global config directory {self.global_configs_base_path}: {e}")
            raise RuntimeError(f"AgentConfigHandler critical failure: Could not create global config directory {self.global_configs_base_path}: {e}")

    def _validate_agent_id_format(self, agent_id: str):
        if not agent_id or ".." in agent_id or "/" in agent_id or "\\" in agent_id:
            logger.error(f"Attempted to use invalid agent_id format: '{agent_id}'")
            raise ValueError(f"Invalid agent_id format: '{agent_id}'")

    def _get_global_agent_config_file_path(self, agent_id: str) -> Path:
        self._validate_agent_id_format(agent_id)
        return self.global_configs_base_path / f"{agent_id}.json"

    def _get_local_agent_configs_base_path(self, session_id: str) -> Path:
        self.session_handler._validate_session_id_format(session_id)
        session_folder_path = self.session_handler._get_session_folder_path(session_id)
        local_agents_path = session_folder_path / SESSION_LOCAL_AGENTS_DIR_NAME
        return local_agents_path

    def _get_local_agent_config_file_path(self, session_id: str, agent_id: str) -> Path:
        self._validate_agent_id_format(agent_id)
        local_configs_base_path = self._get_local_agent_configs_base_path(session_id)
        return local_configs_base_path / f"{agent_id}.json"

    async def _read_agent_config_file(self, file_path: Path, agent_id_expected: str) -> Optional[AgentConfig]:
        if not await asyncio.to_thread(file_path.is_file):
            return None
        
        try:
            def _read_file():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            data = await asyncio.to_thread(_read_file)
            config = AgentConfig(**data)
            if config.agent_id != agent_id_expected:
                logger.warning(f"Agent config file '{file_path}' has mismatched agent_id. Expected: {agent_id_expected}, Found: {config.agent_id}. Ignoring.")
                return None
            return config
        except (json.JSONDecodeError, ValueError) as e: 
            logger.error(f"Corrupted or invalid agent config file found at '{file_path}': {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading agent config file '{file_path}': {e}")
            raise 

    async def _write_agent_config_file(self, file_path: Path, config: AgentConfig):
        await asyncio.to_thread(file_path.parent.mkdir, parents=True, exist_ok=True)
        try:
            def _write_file():
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config.model_dump(mode='json'), f, indent=4)
            await asyncio.to_thread(_write_file)
        except IOError as e:
            logger.error(f"Failed to write agent config to '{file_path}': {e}")
            raise

    async def save_global_agent_config(self, config: AgentConfig):
        file_path = self._get_global_agent_config_file_path(config.agent_id)
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        existing_config = await self.get_global_agent_config(config.agent_id)
        if existing_config:
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
        configs = []
        if not await asyncio.to_thread(self.global_configs_base_path.exists):
            return []

        file_paths = await asyncio.to_thread(list, self.global_configs_base_path.glob("*.json"))
        for file_path in file_paths:
            agent_id = file_path.stem 
            config = await self._read_agent_config_file(file_path, agent_id)
            if config:
                configs.append(config)
        configs.sort(key=lambda c: c.updated_at, reverse=True)
        return configs

    async def delete_global_agent_config(self, agent_id: str) -> bool:
        file_path = self._get_global_agent_config_file_path(agent_id)
        if not await asyncio.to_thread(file_path.is_file):
            logger.info(f"Global agent config '{agent_id}' not found for deletion.")
            return True 
        
        try:
            await asyncio.to_thread(file_path.unlink)
            logger.info(f"Deleted global agent config: {agent_id}")
            return True
        except OSError as e:
            logger.error(f"Failed to delete global agent config '{agent_id}': {e}")
            raise 

    async def save_local_agent_config(self, session_id: str, config: AgentConfig):
        session = await self.session_handler.get_session(session_id)
        if not session:
            raise FileNotFoundError(f"Work Session ID '{session_id}' not found.")

        local_configs_base_path = self._get_local_agent_configs_base_path(session_id)
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
            session = await self.session_handler.get_session(session_id)
            if not session:
                logger.debug(f"Session '{session_id}' not found when trying to get local agent config '{agent_id}'.")
                return None
            
            file_path = self._get_local_agent_config_file_path(session_id, agent_id)
            return await self._read_agent_config_file(file_path, agent_id)
        except FileNotFoundError:
            logger.debug(f"Local agent config file or base path not found for session '{session_id}'.")
            return None
        except ValueError: 
            raise 

    async def list_local_agent_configs(self, session_id: str) -> List[AgentConfig]:
        session = await self.session_handler.get_session(session_id)
        if not session:
            raise FileNotFoundError(f"Work Session ID '{session_id}' not found.")

        local_configs_base_path = self._get_local_agent_configs_base_path(session_id)
        configs = []
        if not await asyncio.to_thread(local_configs_base_path.exists):
            return []

        file_paths = await asyncio.to_thread(list, local_configs_base_path.glob("*.json"))
        for file_path in file_paths:
            agent_id = file_path.stem
            config = await self._read_agent_config_file(file_path, agent_id)
            if config:
                configs.append(config)
        
        configs.sort(key=lambda c: c.updated_at, reverse=True)
        return configs

    async def delete_local_agent_config(self, session_id: str, agent_id: str) -> bool:
        session = await self.session_handler.get_session(session_id)
        if not session:
            raise FileNotFoundError(f"Work Session ID '{session_id}' not found.")

        file_path = self._get_local_agent_config_file_path(session_id, agent_id)
        if not await asyncio.to_thread(file_path.is_file):
            logger.info(f"Local agent config '{agent_id}' for session '{session_id}' not found for deletion.")
            return True 
        
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
                local_config = await self.get_local_agent_config(session_id, agent_id)
                if local_config:
                    logger.debug(f"Resolved agent '{agent_id}' from local session '{session_id}'.")
                    return local_config
            except FileNotFoundError:
                logger.debug(f"Session folder not found for session '{session_id}' during local agent config lookup, falling back to global.")
            except ValueError: 
                logger.warning(f"Invalid session_id '{session_id}' provided for effective agent config lookup. Falling back to global.")

        global_config = await self.get_global_agent_config(agent_id)
        if global_config:
            logger.debug(f"Resolved agent '{agent_id}' from global configuration.")
            return global_config
        
        logger.debug(f"Agent config '{agent_id}' not found globally or locally (if session_id was provided).")
        return None
