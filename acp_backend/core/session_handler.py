# acp_backend/core/session_handler.py
import logging
import uuid
import datetime
import json
import shutil
from pathlib import Path
from typing import List, Optional, TypeVar
import asyncio 

# Import the class for type hinting, but conditionally use the passed instance
from acp_backend.config import Settings as SettingsClass
from acp_backend.config import settings as global_settings_instance # Fallback

from acp_backend.models.work_session_models import WorkSession, CreateWorkSessionRequest, UpdateWorkSessionRequest

logger = logging.getLogger(__name__)

SESSION_MANIFEST_FILENAME = "session_manifest.json"
SESSION_DATA_DIRNAME = "data"
LOCAL_AGENTS_DIR_NAME = "_agents" 

# Type variable for Settings, to allow for None
TSettings = TypeVar('TSettings', bound=SettingsClass)

class SessionHandler:
    """
    Manages creation, retrieval, update, and deletion of work sessions.
    """
    def __init__(self, settings_override: Optional[TSettings] = None):
        current_settings = settings_override if settings_override else global_settings_instance
        
        self.settings = current_settings # Store the settings instance used
        self.sessions_base_dir = self.settings.WORK_SESSIONS_DIR
        
        # DEBUG PRINT REMOVED FROM HERE
        self._ensure_base_directory_exists()
        logger.info(f"SessionHandler initialized. Base directory: {self.sessions_base_dir}")

    def _ensure_base_directory_exists(self):
        try:
            self.sessions_base_dir.mkdir(parents=True, exist_ok=True)
            self.settings.get_global_agent_configs_path().mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.critical(f"SessionHandler critical failure: Could not create base directory {self.sessions_base_dir}: {e}")
            raise RuntimeError(f"SessionHandler critical failure: Could not create base directory {self.sessions_base_dir}: {e}")

    def _validate_session_id_format(self, session_id: str):
        if not session_id or ".." in session_id or "/" in session_id or "\\" in session_id:
            logger.error(f"Attempted to use invalid session_id format: '{session_id}'")
            raise ValueError(f"Invalid session_id format: '{session_id}'")

    def _get_session_folder_path(self, session_id: str) -> Path:
        self._validate_session_id_format(session_id)
        return self.sessions_base_dir / session_id

    def _get_session_manifest_path(self, session_id: str) -> Path:
        return self._get_session_folder_path(session_id) / SESSION_MANIFEST_FILENAME

    def _get_session_data_path(self, session_id: str) -> Path:
        return self._get_session_folder_path(session_id) / SESSION_DATA_DIRNAME

    def _get_session_local_agents_path(self, session_id: str) -> Path:
        return self._get_session_folder_path(session_id) / LOCAL_AGENTS_DIR_NAME

    async def create_session(self, request: CreateWorkSessionRequest) -> WorkSession:
        session_id = str(uuid.uuid4())
        session_folder = self._get_session_folder_path(session_id)
        session_data_folder = self._get_session_data_path(session_id)
        session_agents_folder = self._get_session_local_agents_path(session_id)

        try:
            await asyncio.to_thread(session_folder.mkdir, parents=True, exist_ok=False)
            await asyncio.to_thread(session_data_folder.mkdir, exist_ok=True)
            await asyncio.to_thread(session_agents_folder.mkdir, exist_ok=True)

            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            session_obj = WorkSession(
                session_id=session_id,
                name=request.name,
                description=request.description,
                created_at=now,
                last_accessed=now
            )
            
            manifest_path = self._get_session_manifest_path(session_id)
            
            def _write_manifest():
                with open(manifest_path, 'w', encoding='utf-8') as f:
                    json.dump(session_obj.model_dump(mode='json'), f, indent=4)
            await asyncio.to_thread(_write_manifest)
            
            logger.info(f"Created new session '{session_obj.name}' with ID: {session_id}")
            return session_obj
        except FileExistsError:
            logger.error(f"Attempted to create session with ID '{session_id}' but folder already exists.")
            raise RuntimeError(f"Session with ID '{session_id}' already exists.")
        except IOError as e:
            logger.critical(f"Could not write session manifest for new session '{session_id}': {e}")
            if await asyncio.to_thread(session_folder.exists): 
                await asyncio.to_thread(shutil.rmtree, session_folder)
            raise RuntimeError(f"Could not write session manifest: {e}")
        except Exception as e:
            logger.critical(f"Unexpected error creating session '{session_id}': {e}")
            if await asyncio.to_thread(session_folder.exists): 
                await asyncio.to_thread(shutil.rmtree, session_folder)
            raise

    async def get_session(self, session_id: str) -> Optional[WorkSession]:
        manifest_path = self._get_session_manifest_path(session_id)
        if not await asyncio.to_thread(manifest_path.is_file):
            logger.debug(f"Session manifest not found for ID: {session_id}")
            return None
        
        try:
            def _read_manifest():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            manifest_data = await asyncio.to_thread(_read_manifest)
            session_obj = WorkSession(**manifest_data)
            
            session_obj.last_accessed = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            def _write_updated_manifest():
                with open(manifest_path, 'w', encoding='utf-8') as f:
                    json.dump(session_obj.model_dump(mode='json'), f, indent=4)
            await asyncio.to_thread(_write_updated_manifest)

            logger.debug(f"Retrieved session '{session_id}'. Last accessed updated.")
            return session_obj
        except (json.JSONDecodeError, FileNotFoundError, ValueError) as e:
            logger.error(f"Error loading session manifest for '{session_id}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting session '{session_id}': {e}")
            raise

    async def list_sessions(self) -> List[WorkSession]:
        sessions = []
        try:
            session_folders = await asyncio.to_thread(list, self.sessions_base_dir.iterdir())
        except FileNotFoundError: 
            logger.warning(f"Sessions base directory {self.sessions_base_dir} not found during list_sessions.")
            return []

        for session_folder in session_folders:
            if not await asyncio.to_thread(session_folder.is_dir):
                continue
            if session_folder.name == self.settings.GLOBAL_AGENT_CONFIGS_DIR_NAME:
                continue

            session_id = session_folder.name
            try:
                session = await self.get_session(session_id)
                if session:
                    sessions.append(session)
            except Exception as e:
                logger.warning(f"Skipping corrupted or inaccessible session folder '{session_id}': {e}")
        
        sessions.sort(key=lambda s: s.last_accessed, reverse=True)
        return sessions

    async def update_session(self, session_id: str, update_data: UpdateWorkSessionRequest) -> Optional[WorkSession]:
        session_obj = await self.get_session(session_id)
        if not session_obj:
            logger.warning(f"Attempted to update non-existent session: {session_id}")
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(session_obj, key, value)
        
        manifest_path = self._get_session_manifest_path(session_id)
        
        try:
            def _write_manifest_update():
                with open(manifest_path, 'w', encoding='utf-8') as f:
                    json.dump(session_obj.model_dump(mode='json'), f, indent=4)
            await asyncio.to_thread(_write_manifest_update)
            logger.info(f"Updated session '{session_id}'.")
            return session_obj
        except IOError as e:
            logger.error(f"Error updating session manifest for '{session_id}': {e}")
            raise RuntimeError(f"Failed to update session '{session_id}': {e}")
        except Exception as e:
            logger.error(f"Unexpected error updating session '{session_id}': {e}")
            raise

    async def delete_session(self, session_id: str) -> bool:
        session_folder = self._get_session_folder_path(session_id)
        if not await asyncio.to_thread(session_folder.exists):
            logger.info(f"Attempted to delete non-existent session folder: {session_id}. Returning True as effectively deleted.")
            return True
        
        try:
            await asyncio.to_thread(shutil.rmtree, session_folder)
            logger.info(f"Deleted session folder for ID: {session_id}")
            return True
        except OSError as e:
            logger.error(f"Failed to delete session folder '{session_id}': {e}")
            raise IOError(f"Could not delete session folder '{session_id}': {e}")
        except Exception as e:
            logger.error(f"Unexpected error deleting session '{session_id}': {e}")
            raise
