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
    session_id: Annotated[str, Path(..., description="Session ID for work board operations.")], # This will get session_id from the prefix
    current_settings: SettingsDep,
    current_session_handler: SessionHandlerDep,
):
    if not current_settings.ENABLE_WORK_BOARD_MODULE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{MODULE_NAME} is currently disabled.",
        )
    try:
        session_meta = await current_session_handler.get_session_metadata(session_id)
    except ValueError: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session ID format: {session_id}",
        )

    if not session_meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session ID '{session_id}' not found.",
        )

COMMON_DEPS = [Depends(_check_module_and_session)]

@router.get(
    "/list", # Removed "/{session_id}" as it's in the main app's prefix
    response_model=List[FileNode],
    summary="List Files and Directories",
    tags=[TAG_WORKBOARD],
    dependencies=COMMON_DEPS,
)
async def list_files_in_work_board(
    session_id: Annotated[str, Path(..., description="Session ID.")], # Will be populated from prefix
    fs_manager: FSManagerCheckedDep, 
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
    "/read", # Removed "/{session_id}"
    response_model=ReadFileResponse,
    summary="Read File Content",
    tags=[TAG_WORKBOARD],
    dependencies=COMMON_DEPS,
)
async def read_file_content_from_work_board(
    session_id: Annotated[str, Path(..., description="Session ID.")], # Will be populated from prefix
    path: Annotated[str, Query(..., description="Relative path of the file to read.")], 
    fs_manager: FSManagerCheckedDep, 
):
    try:
        return await fs_manager.read_file(session_id, path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IsADirectoryError as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e: 
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
    "/write", # Removed "/{session_id}"
    response_model=FileNode,
    status_code=status.HTTP_200_OK, 
    summary="Write File Content",
    tags=[TAG_WORKBOARD],
    dependencies=COMMON_DEPS,
)
async def write_file_content_to_work_board(
    session_id: Annotated[str, Path(..., description="Session ID.")], # Will be populated from prefix
    request: Annotated[WriteFileRequest, Body(...)], 
    fs_manager: FSManagerCheckedDep, 
):
    try:
        overwrite = getattr(request, "overwrite", False)
        return await fs_manager.write_file(
            session_id,
            request.path,
            request.content,
            overwrite,
        )
    except FileNotFoundError as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotADirectoryError as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IsADirectoryError as e: 
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
    "/delete", # Removed "/{session_id}"
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete File or Directory",
    tags=[TAG_WORKBOARD],
    dependencies=COMMON_DEPS, 
)
async def delete_work_board_item(
    session_id: Annotated[str, Path(..., description="Session ID.")], # Will be populated from prefix
    path: Annotated[str, Query(..., description="Relative path of the item to delete.")], 
    fs_manager: FSManagerCheckedDep, 
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
    "/mkdir", # Removed "/{session_id}"
    response_model=FileNode,
    status_code=status.HTTP_201_CREATED,
    summary="Create Directory",
    tags=[TAG_WORKBOARD],
    dependencies=COMMON_DEPS,
)
async def create_work_board_directory(
    session_id: Annotated[str, Path(..., description="Session ID.")], # Will be populated from prefix
    request: Annotated[CreateDirectoryRequest, Body(...)], 
    fs_manager: FSManagerCheckedDep, 
):
    try:
        return await fs_manager.create_directory(session_id, request.path)
    except FileNotFoundError as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except NotADirectoryError as e: 
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
    "/move", # Removed "/{session_id}"
    response_model=FileNode,
    summary="Move/Rename File or Directory",
    tags=[TAG_WORKBOARD],
    dependencies=COMMON_DEPS,
)
async def move_work_board_item(
    session_id: Annotated[str, Path(..., description="Session ID.")], # Will be populated from prefix
    request: Annotated[MoveItemRequest, Body(...)], 
    fs_manager: FSManagerCheckedDep, 
):
    try:
        return await fs_manager.move_item(
            session_id, request.source_path, request.destination_path
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except FileExistsError as e: 
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except NotADirectoryError as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IsADirectoryError as e: 
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


