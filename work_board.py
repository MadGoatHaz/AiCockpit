# acp_backend/routers/work_board.py
import asyncio
import logging
from pathlib import Path as PPath # Renamed to avoid conflict with fastapi.Path
from typing import Annotated, List, Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path, # FastAPI's Path
    Query,
    status,
)

from acp_backend.config import AppSettings
from acp_backend.core.fs_manager import FileSystemManager
from acp_backend.core.session_handler import SessionHandler
from acp_backend.dependencies import (
    get_app_settings,
    get_fs_manager,
    get_session_handler,
)
from acp_backend.models.work_board_models import (
    CreateDirectoryRequest,
    FileNode,
    MoveItemRequest,
    ReadFileResponse,
    WriteFileRequest,
)
from acp_backend.models.work_session_models import SessionMetadata


logger = logging.getLogger(__name__)
router = APIRouter()
MODULE_NAME = "WorkBoard Service"
TAG_WORKBOARD = "WorkBoard File System"

# Type Aliases for Dependencies
SettingsDep = Annotated[AppSettings, Depends(get_app_settings)]
SessionHandlerDep = Annotated[SessionHandler, Depends(get_session_handler)]


def _get_fs_manager_checked(
    fs_manager_instance: Annotated[
        Optional[FileSystemManager], Depends(get_fs_manager)
    ],
) -> FileSystemManager:
    if fs_manager_instance is None:
        # This case should ideally be handled by get_fs_manager raising an error
        # or by ensuring get_fs_manager always returns an instance if the app is configured correctly.
        logger.error("FileSystemManager is None in _get_fs_manager_checked. This indicates a setup issue.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="WorkBoard service is not properly initialized (FSManager is None).",
        )
    return fs_manager_instance


FSManagerCheckedDep = Annotated[
    FileSystemManager, Depends(_get_fs_manager_checked)
]


async def _check_module_and_session(
    # Path param must be declared in the dependent function if it's to be used from the path
    # However, FastAPI can also inject path parameters from the main route into dependencies.
    # For clarity, ensure session_id is available to this dependency if needed directly from path.
    # If session_id is taken from the path of the main endpoint, FastAPI handles this.
    session_id: Annotated[str, Path(..., description="Session ID for work board operations.")],
    current_settings: SettingsDep,
    current_session_handler: SessionHandlerDep,
):
    if not current_settings.ENABLE_WORK_BOARD_MODULE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{MODULE_NAME} is currently disabled.",
        )
    try:
        # Ensure session_id is correctly passed or accessible here
        session_meta = await current_session_handler.get_session_metadata(session_id)
    except ValueError: # Specific exception for invalid ID format from SessionHandler
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session ID format: {session_id}",
        )

    if not session_meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session ID '{session_id}' not found.",
        )

# Common dependencies for routes that need session_id from path and module/session checks
# The session_id in _check_module_and_session will be automatically populated by FastAPI
# from the path parameter of the route using this dependency.
COMMON_DEPS = [Depends(_check_module_and_session)]

@router.get(
    "/{session_id}/list", # session_id moved to path for RESTful design
    response_model=List[FileNode],
    summary="List Files and Directories",
    tags=[TAG_WORKBOARD],
    dependencies=COMMON_DEPS,
)
async def list_files_in_work_board(
    session_id: Annotated[str, Path(..., description="Session ID.")],
    fs_manager: FSManagerCheckedDep, # Moved before 'path' to fix SyntaxError
    path: Annotated[str, Query(description="Relative directory path within the session's data root.")] = ".",
):
    try:
        return await fs_manager.list_dir(session_id, path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except NotADirectoryError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IOError as e:
        logger.error(
            f"IOError listing work_board for session {session_id}, path {path}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {str(e)}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error listing work_board for session {session_id}, path {path}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.get(
    "/{session_id}/read", # session_id moved to path
    response_model=ReadFileResponse,
    summary="Read File Content",
    tags=[TAG_WORKBOARD],
    dependencies=COMMON_DEPS,
)
async def read_file_content_from_work_board(
    session_id: Annotated[str, Path(..., description="Session ID.")],
    path: Annotated[str, Query(..., description="Relative path of the file to read.")], # Required query, no Python default
    fs_manager: FSManagerCheckedDep, # Order is OK here as 'path' has no Python default
):
    try:
        return await fs_manager.read_file(session_id, path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IsADirectoryError as e: # Python's built-in error for trying to open/read a directory like a file
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e: # Can be raised by fs_manager for invalid paths or other value errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IOError as e:
        logger.error(
            f"IOError reading file for session {session_id}, path {path}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {str(e)}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error reading file for session {session_id}, path {path}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.post(
    "/{session_id}/write", # session_id moved to path
    response_model=FileNode,
    status_code=status.HTTP_200_OK, # Or HTTP_201_CREATED if a new file is always made
    summary="Write File Content",
    tags=[TAG_WORKBOARD],
    dependencies=COMMON_DEPS,
)
async def write_file_content_to_work_board(
    session_id: Annotated[str, Path(..., description="Session ID.")],
    request: Annotated[WriteFileRequest, Body(...)], # No Python default
    fs_manager: FSManagerCheckedDep, # Order is OK
):
    try:
        # Ensure 'overwrite' attribute is safely accessed if it's optional in WriteFileRequest
        overwrite = getattr(request, "overwrite", False)
        return await fs_manager.write_file(
            session_id,
            request.path,
            request.content,
            overwrite,
        )
    except FileNotFoundError as e: # Raised if parent directory of request.path doesn't exist
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotADirectoryError as e: # Raised if part of request.path is a file, not a directory
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IsADirectoryError as e: # If trying to write to a path that is a directory
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IOError as e:
        logger.error(
            f"IOError writing file for session {session_id}, path {request.path}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {str(e)}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error writing file for session {session_id}, path {request.path}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )

@router.delete(
    "/{session_id}/delete", # session_id moved to path
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete File or Directory",
    tags=[TAG_WORKBOARD],
    dependencies=COMMON_DEPS, # Uses the common dependency check
)
async def delete_work_board_item(
    session_id: Annotated[str, Path(..., description="Session ID.")],
    path: Annotated[str, Query(..., description="Relative path of the item to delete.")], # No Python default
    fs_manager: FSManagerCheckedDep, # Order is OK
):
    try:
        success = await fs_manager.delete_item(session_id, path)
        if not success:
            logger.warning(f"delete_item returned false for session {session_id}, path {path}. Item might not have existed or deletion failed.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found or deletion failed.",
            )
        return None
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IsADirectoryError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot delete directory: {str(e)}")
    except IOError as e:
        logger.error(
            f"IOError deleting item for session {session_id}, path {path}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {str(e)}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error deleting item for session {session_id}, path {path}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )

@router.post(
    "/{session_id}/mkdir", # session_id moved to path
    response_model=FileNode,
    status_code=status.HTTP_201_CREATED,
    summary="Create Directory",
    tags=[TAG_WORKBOARD],
    dependencies=COMMON_DEPS,
)
async def create_work_board_directory(
    session_id: Annotated[str, Path(..., description="Session ID.")],
    request: Annotated[CreateDirectoryRequest, Body(...)], # No Python default
    fs_manager: FSManagerCheckedDep, # Order is OK
):
    try:
        return await fs_manager.create_directory(session_id, request.path)
    except FileNotFoundError as e: # If a parent path component doesn't exist
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except NotADirectoryError as e: # If a component of the path is a file
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IOError as e:
        logger.error(
            f"IOError creating directory for session {session_id}, path {request.path}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {str(e)}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error creating directory for session {session_id}, path {request.path}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.post(
    "/{session_id}/move", # session_id moved to path
    response_model=FileNode,
    summary="Move/Rename File or Directory",
    tags=[TAG_WORKBOARD],
    dependencies=COMMON_DEPS,
)
async def move_work_board_item(
    session_id: Annotated[str, Path(..., description="Session ID.")],
    request: Annotated[MoveItemRequest, Body(...)], # No Python default
    fs_manager: FSManagerCheckedDep, # Order is OK
):
    try:
        return await fs_manager.move_item(
            session_id, request.source_path, request.destination_path
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except FileExistsError as e: # If destination_path already exists
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except NotADirectoryError as e: # If source_path or a component of destination_path is not a directory as expected
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IsADirectoryError as e: # If source is a directory and destination is a file or vice-versa in a way move_item can't handle
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IOError as e:
        logger.error(
            f"IOError moving item for session {session_id}, from {request.source_path} to {request.destination_path}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IOError: {str(e)}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error moving item for session {session_id}, from {request.source_path} to {request.destination_path}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )

