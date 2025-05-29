"""
ACP Backend - Router for Workspace File Management
"""
import logging
import shutil
from pathlib import Path
from typing import Annotated, List

from fastapi import APIRouter, Depends, File, HTTPException, Path as FastApiPath, Query, UploadFile, status

from acp_backend.core.session_handler import SessionHandler
from acp_backend.dependencies import get_session_handler
from acp_backend.models.file_models import FileMetadata, FileNode, DirectoryListing, FileContentUpdateRequest, CreateFileEntityRequest # Added CreateFileEntityRequest

logger = logging.getLogger(__name__)
router = APIRouter()
MODULE_NAME = "Workspace File Management"
TAG_WORKSPACE_FILES = "Workspace Files"

SessionHandlerDep = Annotated[SessionHandler, Depends(get_session_handler)]

@router.post(
    "/sessions/{session_id}/files/upload",
    summary="Upload a file to a workspace session",
    tags=[TAG_WORKSPACE_FILES],
    status_code=status.HTTP_201_CREATED,
    response_model=FileMetadata # Placeholder, adjust as needed
)
async def upload_file_to_session(
    session_id: Annotated[str, FastApiPath(..., description="The ID of the workspace session")],
    file: Annotated[UploadFile, File(..., description="The file to upload")],
    session_handler: SessionHandlerDep,
    relative_path: Annotated[str, Query(description="Relative path within the session's data directory to save the file. Defaults to root.")] = "."
):
    """
    Uploads a file to the specified workspace session's data directory.
    You can specify a relative path within the data directory.
    """
    try:
        # Validate session ID format (basic validation, SessionHandler will do more)
        from uuid import UUID
        try:
            session_uuid = UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session_id format.")

        # Get the session's data root path
        session_data_root = await session_handler.get_session_data_root(session_uuid)
        
        # Construct the full destination path
        # Ensure relative_path is safe and does not traverse upwards (e.g., using "..")
        # For simplicity, FastAPI/Pydantic might handle some of this, but explicit checks are good.
        # A more robust solution would be to resolve the path and ensure it's within session_data_root.
        # Path.resolve() can help here.
        
        # Normalize relative_path: remove leading/trailing slashes, ensure it's relative
        norm_relative_path = Path(relative_path).as_posix().strip('/')
        if norm_relative_path == '.':
            norm_relative_path = '' # Store in root of data dir

        # Prevent path traversal attacks
        # Check if the normalized path attempts to go "up" from the base
        destination_path_check = (Path(session_data_root) / norm_relative_path / file.filename).resolve()
        if not destination_path_check.is_relative_to(session_data_root.resolve()):
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid relative path. Path traversal detected."
            )
        
        destination_path = Path(session_data_root) / norm_relative_path / file.filename
        
        # Create parent directories if they don't exist
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Attempting to upload file '{file.filename}' to '{destination_path}' for session '{session_id}'")

        # Save the file
        try:
            with open(destination_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except IOError as e:
            logger.error(f"Could not write file to '{destination_path}': {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not save file: {e}")
        finally:
            file.file.close()

        logger.info(f"Successfully uploaded file '{file.filename}' to session '{session_id}' at '{destination_path}'")
        
        # For now, return a simple dict. Later, use FileMetadata model.
        return FileMetadata(
            filename=file.filename,
            content_type=file.content_type,
            size=destination_path.stat().st_size, # Get actual size on disk
            path=str(Path(norm_relative_path) / file.filename) # Path relative to session data root
        )

    except HTTPException:
        raise # Re-raise HTTPExceptions directly
    except FileNotFoundError: # Raised by get_session_data_root if session doesn't exist
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session with ID '{session_id}' not found.")
    except Exception as e:
        logger.error(f"Error uploading file to session '{session_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

@router.get(
    "/sessions/{session_id}/files/list",
    summary="List files and folders in a workspace session directory",
    tags=[TAG_WORKSPACE_FILES],
    response_model=DirectoryListing
)
async def list_files_in_session_directory(
    session_id: Annotated[str, FastApiPath(..., description="The ID of the workspace session")],
    session_handler: SessionHandlerDep,
    path: Annotated[str, Query(description="Relative path within the session's data directory to list. Defaults to root.")] = "."
):
    """
    Lists files and folders within a specified relative path of the session's data directory.
    """
    try:
        from uuid import UUID
        try:
            session_uuid = UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session_id format.")

        session_data_root = await session_handler.get_session_data_root(session_uuid)

        # Normalize and validate the requested path
        norm_requested_path_str = Path(path).as_posix().strip('/')
        if norm_requested_path_str == '.':
            norm_requested_path_str = ''
        
        requested_dir_abs = (session_data_root / norm_requested_path_str).resolve()

        # Security check: Ensure the resolved path is within the session_data_root
        if not requested_dir_abs.is_relative_to(session_data_root.resolve()):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path: Access denied.")
        
        if not requested_dir_abs.is_dir():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Path '{norm_requested_path_str}' not found or is not a directory.")

        contents: List[FileNode] = []
        for item in sorted(list(requested_dir_abs.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower())):
            item_relative_path = item.relative_to(session_data_root).as_posix()
            if item.is_dir():
                contents.append(FileNode(id=item_relative_path, name=item.name, path=item_relative_path, type='folder'))
            else:
                contents.append(FileNode(id=item_relative_path, name=item.name, path=item_relative_path, type='file', size=item.stat().st_size))
        
        return DirectoryListing(path=norm_requested_path_str, contents=contents)

    except HTTPException:
        raise
    except FileNotFoundError: # From get_session_data_root
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session with ID '{session_id}' not found.")
    except Exception as e:
        logger.error(f"Error listing files for session '{session_id}' path '{path}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred while listing files: {str(e)}")

# --- File Content Operations ---

@router.get(
    "/sessions/{session_id}/files/content",
    summary="Get the content of a specific file in a workspace session",
    tags=[TAG_WORKSPACE_FILES],
    response_model=str, # Returns raw file content as a string
    responses={
        200: {"content": {"text/plain": {}}},
        400: {"description": "Invalid request (e.g., bad path, path traversal)"},
        404: {"description": "Session or file not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_file_content(
    session_id: Annotated[str, FastApiPath(..., description="The ID of the workspace session")],
    file_path: Annotated[str, Query(..., description="Relative path to the file within the session's data directory.")],
    session_handler: SessionHandlerDep
):
    """
    Retrieves the content of a specific file from the session's data directory.
    The file_path must be a relative path to a file, not a directory.
    """
    from uuid import UUID
    from fastapi.responses import PlainTextResponse
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session_id format.")

    try:
        session_data_root = await session_handler.get_session_data_root(session_uuid)
        
        # Normalize and validate the file_path
        norm_file_path_str = Path(file_path).as_posix().strip('/')
        if not norm_file_path_str or norm_file_path_str == '.':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File path cannot be empty or root.")

        target_file_abs = (session_data_root / norm_file_path_str).resolve()

        # Security check: Ensure the resolved path is within the session_data_root
        if not target_file_abs.is_relative_to(session_data_root.resolve()):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path: Access denied.")
        
        if not target_file_abs.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File '{norm_file_path_str}' not found or is a directory.")

        # Read and return file content
        try:
            content = target_file_abs.read_text(encoding="utf-8")
            return PlainTextResponse(content=content)
        except Exception as e:
            logger.error(f"Error reading file '{target_file_abs}': {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not read file content.")

    except HTTPException:
        raise
    except FileNotFoundError: # From get_session_data_root or if session_data_root itself is missing after check
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session with ID '{session_id}' not found or data directory is inaccessible.")
    except Exception as e:
        logger.error(f"Error getting file content for session '{session_id}' path '{file_path}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred while getting file content: {str(e)}")

@router.put(
    "/sessions/{session_id}/files/content",
    summary="Update the content of a specific file in a workspace session",
    tags=[TAG_WORKSPACE_FILES],
    status_code=status.HTTP_200_OK, # Or 204 No Content if not returning anything
    response_model=FileMetadata # Or a simple success message
)
async def update_file_content(
    session_id: Annotated[str, FastApiPath(..., description="The ID of the workspace session")],
    file_path: Annotated[str, Query(..., description="Relative path to the file within the session's data directory to create or update.")],
    update_request: FileContentUpdateRequest,
    session_handler: SessionHandlerDep
):
    """
    Updates (or creates) the content of a specific file in the session's data directory.
    The file_path must be a relative path to a file.
    """
    from uuid import UUID
    # Import FileContentUpdateRequest here if not already at top level
    from acp_backend.models.file_models import FileContentUpdateRequest

    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session_id format.")

    try:
        session_data_root = await session_handler.get_session_data_root(session_uuid)
        
        norm_file_path_str = Path(file_path).as_posix().strip('/')
        if not norm_file_path_str or norm_file_path_str == '.':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File path cannot be empty or root.")
        
        # Prevent creating directories implicitly with file name (e.g. path="new_dir/file.txt" when new_dir not exists)
        # Client should create directory first if needed via a different endpoint or this logic needs to handle it.
        # For now, let's assume parent directory must exist if not root.
        target_file_abs = (session_data_root / norm_file_path_str).resolve()
        target_file_parent_abs = target_file_abs.parent

        # Security check: Ensure the resolved path is within the session_data_root
        if not target_file_abs.is_relative_to(session_data_root.resolve()):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path: Access denied.")
        
        # Ensure parent directory exists
        if not target_file_parent_abs.is_dir() or not target_file_parent_abs.is_relative_to(session_data_root.resolve()):
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Parent directory for '{norm_file_path_str}' does not exist or is invalid.")

        # Prevent writing to a directory path
        if target_file_abs.is_dir():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot write content to a directory path: '{norm_file_path_str}'.")

        # Write file content
        try:
            target_file_abs.write_text(update_request.content, encoding="utf-8")
            logger.info(f"Successfully wrote content to file '{target_file_abs}' for session '{session_id}'")
            
            # Construct FileMetadata for response
            # Note: content_type isn't known here without more complex logic or input
            # File size might be 0 if content is empty string.
            return FileMetadata(
                filename=target_file_abs.name,
                path=str(target_file_abs.relative_to(session_data_root)),
                # size=target_file_abs.stat().st_size # This would require another stat call, maybe not needed for PUT response
            )

        except Exception as e:
            logger.error(f"Error writing file '{target_file_abs}': {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not write file content.")

    except HTTPException:
        raise
    except FileNotFoundError: # From get_session_data_root
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session with ID '{session_id}' not found.")
    except Exception as e:
        logger.error(f"Error updating file content for session '{session_id}' path '{file_path}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

@router.post(
    "/sessions/{session_id}/files/create",
    summary="Create a new file or folder in a workspace session",
    tags=[TAG_WORKSPACE_FILES],
    status_code=status.HTTP_201_CREATED,
    response_model=FileNode # Return the created FileNode
)
async def create_file_or_folder(
    session_id: Annotated[str, FastApiPath(..., description="The ID of the workspace session")],
    create_request: CreateFileEntityRequest,
    session_handler: SessionHandlerDep
):
    """
    Creates a new file or folder at the specified relative path within the session's data directory.
    - `path`: The relative path (e.g., "new_folder/my_file.txt" or "new_directory").
    - `type`: Must be "file" or "folder".
    If creating a file, it will be empty. If creating a folder, it will be an empty directory.
    Parent directories in the path must exist.
    """
    from uuid import UUID
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session_id format.")

    if create_request.type not in ["file", "folder"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid entity type. Must be 'file' or 'folder'.")

    try:
        session_data_root = await session_handler.get_session_data_root(session_uuid)
        
        norm_entity_path_str = Path(create_request.path).as_posix().strip('/')
        if not norm_entity_path_str or norm_entity_path_str == '.':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Entity path cannot be empty or root.")

        target_entity_abs = (session_data_root / norm_entity_path_str).resolve()

        # Security check: Ensure the resolved path is within the session_data_root
        if not target_entity_abs.is_relative_to(session_data_root.resolve()):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path: Access denied.")
        
        # Check if parent directory exists
        parent_dir_abs = target_entity_abs.parent
        if not parent_dir_abs.is_dir() or not parent_dir_abs.is_relative_to(session_data_root.resolve()):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Parent directory for '{norm_entity_path_str}' does not exist or is invalid.")

        # Check if entity already exists
        if target_entity_abs.exists():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Entity '{norm_entity_path_str}' already exists.")

        try:
            if create_request.type == "file":
                target_entity_abs.touch() # Creates an empty file
                logger.info(f"Successfully created file '{target_entity_abs}' for session '{session_id}'")
            elif create_request.type == "folder":
                target_entity_abs.mkdir()
                logger.info(f"Successfully created folder '{target_entity_abs}' for session '{session_id}'")
            
            return FileNode(
                id=str(target_entity_abs.relative_to(session_data_root)), # ID can be the relative path
                name=target_entity_abs.name,
                path=str(target_entity_abs.relative_to(session_data_root)),
                type=create_request.type,
                # children=[] if create_request.type == "folder" else None # No need to list children here
            )

        except Exception as e:
            logger.error(f"Error creating entity '{target_entity_abs}': {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not create {create_request.type}.")

    except HTTPException:
        raise
    except FileNotFoundError: # From get_session_data_root
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session with ID '{session_id}' not found.")
    except Exception as e:
        logger.error(f"Error creating entity for session '{session_id}' path '{create_request.path}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

@router.delete(
    "/sessions/{session_id}/files/delete",
    summary="Delete a file or folder in a workspace session",
    tags=[TAG_WORKSPACE_FILES],
    status_code=status.HTTP_204_NO_CONTENT 
)
async def delete_file_or_folder(
    session_id: Annotated[str, FastApiPath(..., description="The ID of the workspace session")],
    item_path: Annotated[str, Query(..., description="Relative path to the file or folder to delete.")],
    item_type: Annotated[str, Query(..., description="Type of item to delete: 'file' or 'folder'.")],
    session_handler: SessionHandlerDep
):
    """
    Deletes a file or a folder (recursively if a folder) at the specified relative path.
    - `item_path`: Relative path to the item (e.g., "my_folder/my_file.txt" or "my_folder_to_delete").
    - `item_type`: Should be 'file' or 'folder' to confirm intention.
    """
    from uuid import UUID
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session_id format.")

    if item_type not in ["file", "folder"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid item_type. Must be 'file' or 'folder'.")

    try:
        session_data_root = await session_handler.get_session_data_root(session_uuid)
        
        norm_item_path_str = Path(item_path).as_posix().strip('/')
        if not norm_item_path_str or norm_item_path_str == '.': # Prevent deleting root
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item path cannot be empty or root.")

        target_item_abs = (session_data_root / norm_item_path_str).resolve()

        # Security check
        if not target_item_abs.is_relative_to(session_data_root.resolve()) or target_item_abs == session_data_root.resolve():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path: Access denied or attempt to delete root.")
        
        if not target_item_abs.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item '{norm_item_path_str}' not found.")

        try:
            if item_type == "file":
                if not target_item_abs.is_file():
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Item '{norm_item_path_str}' is not a file as specified.")
                target_item_abs.unlink()
                logger.info(f"Successfully deleted file '{target_item_abs}' for session '{session_id}'")
            elif item_type == "folder":
                if not target_item_abs.is_dir():
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Item '{norm_item_path_str}' is not a folder as specified.")
                shutil.rmtree(target_item_abs) # Recursively deletes directory
                logger.info(f"Successfully deleted folder '{target_item_abs}' for session '{session_id}'")
            
            # No content to return for 204
            return

        except Exception as e:
            logger.error(f"Error deleting item '{target_item_abs}': {e}", exc_info=True)
            # Check if it was a permission error or other FS issue
            if isinstance(e, PermissionError):
                 raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permission denied when trying to delete {item_type} '{norm_item_path_str}'.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not delete {item_type} '{norm_item_path_str}'. {str(e)}")

    except HTTPException:
        raise
    except FileNotFoundError: # From get_session_data_root
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session with ID '{session_id}' not found.")
    except Exception as e:
        logger.error(f"Error deleting item for session '{session_id}' path '{item_path}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

# Add other file management endpoints here (list, download, delete) 