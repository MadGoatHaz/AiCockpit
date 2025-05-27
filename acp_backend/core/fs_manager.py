# acp_backend/core/fs_manager.py
import os
import logging
import datetime
import shutil 
from pathlib import Path 
from typing import List, Optional 
import sys 
import asyncio # Ensure asyncio is imported

from acp_backend.models.work_board_models import FileNode, ReadFileResponse, WriteFileRequest
from acp_backend.core.session_handler import SessionHandler # Import the class

logger = logging.getLogger(__name__)

class FileSystemManager:
    def __init__(self, session_handler_instance: SessionHandler): 
        self.session_handler = session_handler_instance 
        logger.info(f"FileSystemManager initialized with session_handler: {type(session_handler_instance)}")

    def _get_session_data_root(self, session_id: str) -> Path: 
        if not hasattr(self, 'session_handler') or self.session_handler is None: 
            raise AttributeError("'FileSystemManager' instance has no valid 'session_handler' attribute")
        
        try:
            # _get_session_data_path is synchronous in SessionHandler as it constructs a path
            session_data_path_str_or_path = self.session_handler._get_session_data_path(session_id)
            session_data_path = Path(session_data_path_str_or_path)
        except ValueError as e: 
            raise FileNotFoundError(f"Invalid session ID format for WorkBoard: {session_id}. Details: {e}") from e
        
        # These are blocking IO, ensure they are handled correctly if this method is called from async
        # However, this method itself is synchronous. If called by an async method, that caller should use to_thread.
        if session_data_path.exists() and session_data_path.is_dir():
            return session_data_path.resolve() 
        
        log_msg = f"Session data path for session_id '{session_id}' problem: {session_data_path}"
        if not session_data_path.exists(): log_msg += " (does not exist)"
        else: log_msg += " (not a directory)"
        logger.error(log_msg)
        raise FileNotFoundError(f"Work session '{session_id}' data directory not accessible. {log_msg}")

    def _resolve_path_within_session(self, session_id: str, relative_path_str: str) -> Path: 
        session_root = self._get_session_data_root(session_id) 
        if not relative_path_str or relative_path_str == ".":
            normalized_relative_path = Path() 
        else:
            cleaned_relative_path = relative_path_str.lstrip('/\\')
            path_obj = Path(cleaned_relative_path)
            normalized_relative_path = path_obj
        absolute_path = (session_root / normalized_relative_path).resolve()
        
        # Check if absolute_path is within session_root
        # Path.is_relative_to() is available in Python 3.9+
        # For broader compatibility or explicit check:
        if not str(absolute_path).startswith(str(session_root.resolve())):
            logger.error(f"Path traversal: session='{session_id}', rel='{relative_path_str}'. Resolved to '{absolute_path}' outside '{session_root}'.")
            raise FileNotFoundError(f"Access denied: Path '{relative_path_str}' is outside session data directory.")
        return absolute_path

    async def list_dir(self, session_id: str, relative_path: str = ".") -> List[FileNode]:
        absolute_dir_path = self._resolve_path_within_session(session_id, relative_path)
        if not await asyncio.to_thread(absolute_dir_path.exists): 
            raise FileNotFoundError(f"Directory not found: {relative_path}")
        if not await asyncio.to_thread(absolute_dir_path.is_dir): 
            raise NotADirectoryError(f"Not a directory: {relative_path}")
        
        nodes: List[FileNode] = []
        session_data_root_path = self._get_session_data_root(session_id) # This is sync
        
        try:
            # iterdir can be blocking on very large directories
            child_paths = await asyncio.to_thread(list, absolute_dir_path.iterdir())
            for item_path in child_paths: 
                item_rel_path_from_session_data_root = item_path.relative_to(session_data_root_path)
                try:
                    stat_info = await asyncio.to_thread(item_path.stat)
                    is_dir = await asyncio.to_thread(item_path.is_dir)
                    nodes.append(FileNode(
                        name=item_path.name,
                        path=str(item_rel_path_from_session_data_root).replace(os.path.sep, '/'),
                        is_dir=is_dir,
                        size_bytes=stat_info.st_size if not is_dir else None,
                        modified_at=datetime.datetime.fromtimestamp(stat_info.st_mtime, tz=datetime.timezone.utc).isoformat()
                    ))
                except OSError as e_stat: 
                    logger.error(f"Error stating {item_path}: {e_stat}", exc_info=True)
            nodes.sort(key=lambda x: (not x.is_dir, x.name.lower()))
            return nodes
        except OSError as e_listdir:
            logger.error(f"Error listing dir {absolute_dir_path}: {e_listdir}", exc_info=True)
            raise IOError(f"Could not read dir '{relative_path}': {e_listdir}") from e_listdir

    async def read_file(self, session_id: str, relative_path: str) -> ReadFileResponse:
        absolute_file_path = self._resolve_path_within_session(session_id, relative_path)
        if not await asyncio.to_thread(absolute_file_path.exists): 
            raise FileNotFoundError(f"File not found: {relative_path}")
        if not await asyncio.to_thread(absolute_file_path.is_file): 
            raise IsADirectoryError(f"Path is a directory: {relative_path}")
        try:
            content = await asyncio.to_thread(absolute_file_path.read_text, encoding="utf-8")
            return ReadFileResponse(path=relative_path.replace(os.path.sep, '/'), content=content, encoding="utf-8")
        except UnicodeDecodeError as e: 
            raise ValueError(f"Cannot decode file '{relative_path}': {e}") from e
        except IOError as e: 
            raise IOError(f"Could not read file '{relative_path}': {e}") from e

    async def write_file(self, session_id: str, request: WriteFileRequest) -> FileNode:
        absolute_file_path = self._resolve_path_within_session(session_id, request.path)
        try:
            parent_dir = absolute_file_path.parent
            if await asyncio.to_thread(parent_dir.exists) and not await asyncio.to_thread(parent_dir.is_dir):
                raise NotADirectoryError(f"Parent path '{parent_dir.relative_to(self._get_session_data_root(session_id))}' is a file.")
            await asyncio.to_thread(parent_dir.mkdir, parents=True, exist_ok=True)
            
            await asyncio.to_thread(absolute_file_path.write_text, request.content, encoding=request.encoding)
            stat_info = await asyncio.to_thread(absolute_file_path.stat)
            return FileNode(
                name=absolute_file_path.name, path=request.path.replace(os.path.sep, '/'), is_dir=False,
                size_bytes=stat_info.st_size,
                modified_at=datetime.datetime.fromtimestamp(stat_info.st_mtime, tz=datetime.timezone.utc).isoformat()
            )
        except IOError as e: 
            raise IOError(f"Could not write file '{request.path}': {e}") from e

    async def delete_item(self, session_id: str, relative_path: str) -> bool:
        absolute_item_path = self._resolve_path_within_session(session_id, relative_path)
        if not await asyncio.to_thread(absolute_item_path.exists): 
            return True 
        try:
            if await asyncio.to_thread(absolute_item_path.is_dir): 
                await asyncio.to_thread(shutil.rmtree, absolute_item_path)
            else: 
                await asyncio.to_thread(absolute_item_path.unlink)
            return True
        except OSError as e: 
            raise IOError(f"Could not delete '{relative_path}': {e}") from e

    async def create_directory(self, session_id: str, relative_path: str) -> FileNode:
        absolute_dir_path = self._resolve_path_within_session(session_id, relative_path)
        if await asyncio.to_thread(absolute_dir_path.exists):
            if await asyncio.to_thread(absolute_dir_path.is_dir): 
                stat_info = await asyncio.to_thread(absolute_dir_path.stat)
                return FileNode(name=absolute_dir_path.name, path=relative_path.replace(os.path.sep, '/'), is_dir=True,
                                modified_at=datetime.datetime.fromtimestamp(stat_info.st_mtime, tz=datetime.timezone.utc).isoformat())
            else: 
                raise FileExistsError(f"Path exists as a file: {relative_path}")
        try:
            await asyncio.to_thread(absolute_dir_path.mkdir, parents=True, exist_ok=True) # exist_ok=True to be idempotent if called multiple times for same path
            stat_info = await asyncio.to_thread(absolute_dir_path.stat)
            return FileNode(name=absolute_dir_path.name, path=relative_path.replace(os.path.sep, '/'), is_dir=True,
                            modified_at=datetime.datetime.fromtimestamp(stat_info.st_mtime, tz=datetime.timezone.utc).isoformat())
        except OSError as e: 
            raise IOError(f"Could not create dir '{relative_path}': {e}") from e

    async def move_item(self, session_id: str, source_relative_path: str, destination_relative_path: str) -> FileNode:
        abs_source_path = self._resolve_path_within_session(session_id, source_relative_path)
        abs_destination_path = self._resolve_path_within_session(session_id, destination_relative_path)
        if not await asyncio.to_thread(abs_source_path.exists): 
            raise FileNotFoundError(f"Source path not found: {source_relative_path}")
        if await asyncio.to_thread(abs_destination_path.exists): 
            raise FileExistsError(f"Destination path already exists: {destination_relative_path}")
        try:
            dest_parent_dir = abs_destination_path.parent
            if await asyncio.to_thread(dest_parent_dir.exists) and not await asyncio.to_thread(dest_parent_dir.is_dir):
                 raise NotADirectoryError(f"Parent of destination '{dest_parent_dir.relative_to(self._get_session_data_root(session_id))}' is a file.")
            await asyncio.to_thread(dest_parent_dir.mkdir, parents=True, exist_ok=True)
            
            await asyncio.to_thread(shutil.move, str(abs_source_path), str(abs_destination_path)) 
            stat_info = await asyncio.to_thread(abs_destination_path.stat)
            is_dir = await asyncio.to_thread(abs_destination_path.is_dir)
            return FileNode(
                name=abs_destination_path.name, path=destination_relative_path.replace(os.path.sep, '/'), is_dir=is_dir,
                size_bytes=stat_info.st_size if not is_dir else None,
                modified_at=datetime.datetime.fromtimestamp(stat_info.st_mtime, tz=datetime.timezone.utc).isoformat()
            )
        except (OSError, IOError) as e: 
            raise IOError(f"Could not move '{source_relative_path}' to '{destination_relative_path}': {e}") from e
