# acp_backend/core/session_handler.py
import json
import logging
import shutil
import uuid
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

from pydantic import ValidationError

# Correctly import AppSettings from config.py
# If SessionHandler needs to know the type of the settings object,
# or access app_settings directly (though it's better if config is passed via __init__).
from acp_backend.config import AppSettings # Changed from 'Settings as SettingsClass'
# If you need the app_settings instance directly here (less common for a handler):
# from acp_backend.config import app_settings

from acp_backend.models.work_session_models import (
    SessionCreate,
    SessionMetadata,
    SessionUpdate,
)
from acp_backend.models.ai_config_models import AIModelSessionConfig # Added import

logger = logging.getLogger(__name__)

# Name of the manifest file within each session directory
SESSION_MANIFEST_FILENAME = "session_manifest.json"
# Name of the directory within each session for local agent configurations
SESSION_AGENTS_DIRNAME = "_agents"
# Name of the primary data directory within each session
SESSION_DATA_DIRNAME = "data"
# Name of the AI model configuration file within each session directory
SESSION_AI_CONFIG_FILENAME = "ai_config.json" # Added


class SessionHandler:
    """
    Manages work sessions, including their creation, deletion,
    and metadata persistence on the file system.
    """

    def __init__(self, base_dir: str | Path):
        """
        Initializes the SessionHandler.

        Args:
            base_dir: The base directory where all work sessions will be stored.
                      Each session will have its own subdirectory within this base_dir.
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"SessionHandler initialized. Work sessions base directory: {self.base_dir}")

    def _validate_session_id_format(self, session_id: uuid.UUID) -> None:
        """Basic validation for session_id string format to prevent path traversal."""
        session_id_str = str(session_id) # Ensure it's a string for checks
        if not session_id_str or ".." in session_id_str or "/" in session_id_str or "\\" in session_id_str:
            logger.error(f"Invalid session_id format attempt: {session_id_str}")
            raise ValueError(f"Invalid session_id format: {session_id_str}")

    def _get_session_path(self, session_id: uuid.UUID) -> Path:
        """Returns the path to a specific session's directory."""
        self._validate_session_id_format(session_id) # Added validation call
        return self.base_dir / str(session_id)

    def _get_manifest_path(self, session_id: uuid.UUID) -> Path:
        """Returns the path to a session's manifest file."""
        return self._get_session_path(session_id) / SESSION_MANIFEST_FILENAME

    def _get_session_agents_path(self, session_id: uuid.UUID) -> Path:
        """Returns the path to a session's local agent configurations directory."""
        return self._get_session_path(session_id) / SESSION_AGENTS_DIRNAME

    def _get_session_data_path(self, session_id: uuid.UUID) -> Path:
        """Returns the path to a session's primary data directory."""
        return self._get_session_path(session_id) / SESSION_DATA_DIRNAME

    def _get_session_ai_config_path(self, session_id: uuid.UUID) -> Path: # Added method
        """Returns the path to a session's AI model configuration file."""
        return self._get_session_path(session_id) / SESSION_AI_CONFIG_FILENAME

    async def _read_manifest(self, session_id: uuid.UUID) -> Optional[SessionMetadata]:
        """Reads and validates a session's manifest file."""
        manifest_path = self._get_manifest_path(session_id)
        if not await asyncio.to_thread(manifest_path.is_file):
            return None
        try:
            def _sync_read():
                with open(manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            data = await asyncio.to_thread(_sync_read)
            # Ensure session_id from manifest matches the directory name (and is a UUID)
            if "id" not in data or str(uuid.UUID(data["id"])) != str(session_id):
                logger.warning(
                    f"Session ID mismatch in manifest {manifest_path} "
                    f"(expected {session_id}, got {data.get('id')}). Treating as invalid."
                )
                # Optionally, repair or delete the manifest
                return None
            return SessionMetadata(**data)
        except (json.JSONDecodeError, ValidationError, TypeError) as e:
            logger.error(f"Error reading or validating manifest {manifest_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reading manifest {manifest_path}: {e}", exc_info=True)
            return None


    async def _write_manifest(self, session_id: uuid.UUID, metadata: SessionMetadata) -> bool:
        """Writes a session's metadata to its manifest file."""
        session_path = self._get_session_path(session_id)
        await asyncio.to_thread(session_path.mkdir, parents=True, exist_ok=True) # Ensure session directory exists
        manifest_path = self._get_manifest_path(session_id)
        try:
            # Ensure the ID in metadata matches the session_id being written to
            if str(metadata.id) != str(session_id):
                logger.error(f"Attempted to write manifest with mismatched ID: metadata.id={metadata.id}, session_id={session_id}")
                # Raise an error or handle as appropriate, e.g., force metadata.id = session_id
                # For now, let's assume this shouldn't happen if called correctly.
                # metadata.id = session_id # Or raise error
                pass # Let it write, but this is a sign of an issue elsewhere

            def _sync_write():
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(metadata.model_dump(mode="json"), f, indent=4)
            await asyncio.to_thread(_sync_write)
            return True
        except Exception as e:
            logger.error(f"Error writing manifest {manifest_path}: {e}", exc_info=True)
            return False

    async def create_session(self, session_create_data: SessionCreate) -> Optional[SessionMetadata]:
        """
        Creates a new work session.
        Generates a unique ID, creates a directory structure, and writes a manifest file.
        """
        session_id = uuid.uuid4()
        session_path = self._get_session_path(session_id)
        try:
            await asyncio.to_thread(session_path.mkdir, parents=True, exist_ok=False) # exist_ok=False to ensure it's new
            
            # Create subdirectories for agents and data
            await asyncio.to_thread(self._get_session_agents_path(session_id).mkdir, parents=True, exist_ok=True)
            await asyncio.to_thread(self._get_session_data_path(session_id).mkdir, parents=True, exist_ok=True)

            now = datetime.now(timezone.utc)
            metadata = SessionMetadata(
                id=session_id,
                name=session_create_data.name,
                description=session_create_data.description,
                created_at=now,
                updated_at=now,
                # Initialize custom_ui_settings if your model defines it
                # custom_ui_settings=session_create_data.custom_ui_settings or {} 
            )
            if await self._write_manifest(session_id, metadata):
                logger.info(f"Created new session '{metadata.name}' with ID: {session_id} at {session_path}")
                return metadata
            else:
                # Cleanup if manifest write fails
                await asyncio.to_thread(shutil.rmtree, session_path, ignore_errors=True)
                logger.error(f"Failed to write manifest for new session {session_id}, cleaned up directory.")
                return None
        except FileExistsError:
            logger.error(f"Session directory {session_path} already exists for ID {session_id}. This should not happen with UUIDs.")
            return None # Or retry with a new UUID, though highly unlikely
        except Exception as e:
            logger.error(f"Error creating session directory {session_path}: {e}", exc_info=True)
            # Attempt cleanup if partial creation occurred
            if await asyncio.to_thread(session_path.exists):
                await asyncio.to_thread(shutil.rmtree, session_path, ignore_errors=True)
            return None

    async def get_session_metadata(self, session_id: uuid.UUID) -> Optional[SessionMetadata]:
        """Retrieves a session's metadata by its ID."""
        metadata = await self._read_manifest(session_id)
        if metadata:
            logger.debug(f"Retrieved metadata for session ID: {session_id}")
        else:
            logger.warning(f"No valid manifest found for session ID: {session_id}")
        return metadata

    async def list_sessions(self) -> List[SessionMetadata]:
        """Lists all available work sessions by reading their manifest files."""
        sessions = []
        for item in self.base_dir.iterdir():
            if await asyncio.to_thread(item.is_dir):
                try:
                    session_uuid = uuid.UUID(item.name) # Check if dirname is a valid UUID
                    metadata = await self._read_manifest(session_uuid)
                    if metadata:
                        sessions.append(metadata)
                except ValueError:
                    # Not a UUID named directory, skip
                    logger.debug(f"Skipping directory {item.name}, not a valid session ID format.")
                    continue
        logger.info(f"Found {len(sessions)} valid sessions in {self.base_dir}")
        return sorted(sessions, key=lambda s: s.created_at, reverse=True) # Sort by creation date

    async def update_session_metadata(
        self, session_id: uuid.UUID, session_update_data: SessionUpdate
    ) -> Optional[SessionMetadata]:
        """
        Updates a session's metadata.
        Only fields present in SessionUpdate will be modified.
        The 'updated_at' timestamp is automatically set.
        """
        metadata = await self._read_manifest(session_id)
        if not metadata:
            logger.warning(f"Cannot update session {session_id}: manifest not found or invalid.")
            return None

        update_data_dict = session_update_data.model_dump(exclude_unset=True)
        
        # If custom_ui_settings is part of SessionUpdate and SessionMetadata
        # current_custom_settings = metadata.custom_ui_settings or {}
        # new_custom_settings = update_data_dict.pop("custom_ui_settings", None)
        # if new_custom_settings is not None:
        #     current_custom_settings.update(new_custom_settings)
        #     metadata.custom_ui_settings = current_custom_settings
        
        # Update other fields
        for key, value in update_data_dict.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)
            else:
                logger.warning(f"Attempted to update non-existent field '{key}' in session {session_id}")


        metadata.updated_at = datetime.now(timezone.utc)
        
        if await self._write_manifest(session_id, metadata):
            logger.info(f"Updated metadata for session ID: {session_id}")
            return metadata
        else:
            logger.error(f"Failed to write updated manifest for session {session_id}")
            return None # Or return the old metadata if write failed?

    async def delete_session(self, session_id: uuid.UUID) -> bool:
        """
        Deletes a work session entirely, including its directory and all contents.
        Returns True if successful, False otherwise.
        """
        session_path = self._get_session_path(session_id)
        if not await asyncio.to_thread(session_path.is_dir):
            logger.warning(f"Cannot delete session {session_id}: directory {session_path} not found.")
            return False
        try:
            await asyncio.to_thread(shutil.rmtree, session_path)
            logger.info(f"Successfully deleted session ID: {session_id} from {session_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting session directory {session_path}: {e}", exc_info=True)
            return False

    # --- Methods for managing session-specific AI model configurations ---

    async def get_ai_model_session_config(self, session_id: uuid.UUID) -> Optional[AIModelSessionConfig]: # Added method
        """Reads a session's AI model configuration file."""
        config_path = self._get_session_ai_config_path(session_id)
        if not await asyncio.to_thread(config_path.is_file):
            logger.debug(f"AI model config not found for session {session_id} at {config_path}, returning None.")
            return None # No config file means no specific config set
        try:
            def _sync_read_ai_config():
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            data = await asyncio.to_thread(_sync_read_ai_config)
            return AIModelSessionConfig(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Error reading or validating AI model config {config_path} for session {session_id}: {e}")
            return None # Corrupted or invalid file
        except Exception as e:
            logger.error(f"Unexpected error reading AI model config {config_path} for session {session_id}: {e}", exc_info=True)
            return None

    async def update_ai_model_session_config( # Added method
        self, session_id: uuid.UUID, config_update_data: AIModelSessionConfig
    ) -> Optional[AIModelSessionConfig]:
        """
        Updates or creates a session's AI model configuration.
        The 'updated_at' timestamp on the session manifest is also touched.
        """
        # First, ensure the session itself exists by trying to read its manifest
        session_metadata = await self.get_session_metadata(session_id)
        if not session_metadata:
            logger.warning(f"Cannot update AI model config for non-existent session {session_id}.")
            return None

        session_path = self._get_session_path(session_id)
        await asyncio.to_thread(session_path.mkdir, parents=True, exist_ok=True) # Ensure session directory exists
        config_path = self._get_session_ai_config_path(session_id)

        # Read existing config to merge if necessary, or create new
        # For simplicity, this will overwrite with new data if fields are None in request.
        # A more nuanced merge could be done if AIModelSessionConfig had many fields and partial updates were common.
        # current_config = await self.get_ai_model_session_config(session_id)
        # if current_config:
        #     updated_data = current_config.model_copy(update=config_update_data.model_dump(exclude_none=True))
        # else:
        #     updated_data = config_update_data

        # We'll just use the provided config_update_data directly.
        # Ensure all fields are present even if None, as Pydantic model_dump by default excludes None.
        # config_to_write = config_update_data.model_dump(exclude_none=False) 
        # Actually, let's ensure that if a field is not provided in the update, it's not clearing existing one
        
        existing_config_dict = {}
        existing_config = await self.get_ai_model_session_config(session_id)
        if existing_config:
            existing_config_dict = existing_config.model_dump()

        update_dict = config_update_data.model_dump(exclude_unset=True) # Only get provided fields
        final_config_dict = {**existing_config_dict, **update_dict}
        final_config = AIModelSessionConfig(**final_config_dict)


        try:
            def _sync_write_ai_config():
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(final_config.model_dump(mode="json"), f, indent=4)
            await asyncio.to_thread(_sync_write_ai_config)
            logger.info(f"Updated AI model config for session {session_id} at {config_path}")

            # Touch the main session manifest's updated_at timestamp
            session_metadata.updated_at = datetime.now(timezone.utc)
            await self._write_manifest(session_id, session_metadata)
            
            return final_config
        except Exception as e:
            logger.error(f"Error writing AI model config {config_path} for session {session_id}: {e}", exc_info=True)
            return None

    # --- Methods for managing session-specific agent configurations ---
    async def get_local_agent_configs_path(self, session_id: uuid.UUID) -> Path:
        """Gets the path to the local agent configurations directory for a session."""
        path = self._get_session_agents_path(session_id)
        await asyncio.to_thread(path.mkdir, parents=True, exist_ok=True) # Ensure it exists
        return path

    # --- Methods for managing session data directory ---
    async def get_session_data_root(self, session_id: uuid.UUID) -> Path:
        """
        Gets the root path of the data directory for a given session.
        Ensures the directory exists.
        """
        data_path = self._get_session_data_path(session_id)
        await asyncio.to_thread(data_path.mkdir, parents=True, exist_ok=True) # Ensure it exists
        return data_path
