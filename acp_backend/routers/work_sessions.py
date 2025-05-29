# acp_backend/routers/work_sessions.py
import logging
from typing import List, Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from acp_backend.config import AppSettings
from acp_backend.core.session_handler import SessionHandler
from acp_backend.dependencies import get_app_settings, get_session_handler
from acp_backend.models.work_session_models import (
    SessionCreate,
    SessionMetadata,
    SessionUpdate,
)
from acp_backend.models.ai_config_models import AIModelSessionConfig

logger = logging.getLogger(__name__)
router = APIRouter()
MODULE_NAME = "Work Sessions Service"
TAG_SESSIONS = "Work Session Management"

# Type Aliases for Dependencies
SettingsDep = Annotated[AppSettings, Depends(get_app_settings)]
SessionHandlerDep = Annotated[SessionHandler, Depends(get_session_handler)]


def _check_module_enabled(current_settings: SettingsDep):
    if not current_settings.ENABLE_WORK_SESSIONS_MODULE:
        logger.warning(f"{MODULE_NAME} is disabled in configuration.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{MODULE_NAME} is currently disabled.",
        )


def get_session_handler_checked(
    session_handler_instance: SessionHandlerDep,
) -> SessionHandler:
    if session_handler_instance is None:
        logger.critical(
            "SessionHandler is None after module enabled check. This indicates a DI or initialization issue."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Work Sessions service is not properly initialized.",
        )
    return session_handler_instance


SessionHandlerCheckedDep = Annotated[
    SessionHandler, Depends(get_session_handler_checked)
]


@router.post(
    "/",
    response_model=SessionMetadata,
    status_code=status.HTTP_201_CREATED,
    summary="Create a New Work Session",
    tags=[TAG_SESSIONS],
    dependencies=[Depends(_check_module_enabled)],
)
async def create_new_work_session(
    request: Annotated[SessionCreate, Body(...)],
    handler: SessionHandlerCheckedDep,
):
    logger.info(f"Request to create new work session with name: '{request.name}'")
    try:
        new_session_meta = await handler.create_session(request)
        if not new_session_meta:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session.",
            )
        logger.info(
            f"Work session '{new_session_meta.name}' (ID: {new_session_meta.id}) created successfully."
        )
        return new_session_meta
    except RuntimeError as e:
        logger.error(
            f"Runtime error creating work session '{request.name}': {e}", exc_info=True
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(
            f"Unexpected error creating work session '{request.name}': {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get(
    "/",
    response_model=List[SessionMetadata],
    summary="List All Work Sessions",
    tags=[TAG_SESSIONS],
    dependencies=[Depends(_check_module_enabled)],
)
async def list_all_work_sessions(handler: SessionHandlerCheckedDep):
    logger.debug("Request to list all work sessions.")
    try:
        sessions_meta = await handler.list_sessions()
        logger.debug(f"Returning {len(sessions_meta)} work sessions.")
        return sessions_meta
    except IOError as e:
        logger.error(f"I/O error listing work sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions due to I/O error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error listing work sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list work sessions: {str(e)}",
        )


@router.get(
    "/{session_id}",
    response_model=SessionMetadata,
    summary="Get Details of a Specific Work Session",
    tags=[TAG_SESSIONS],
    dependencies=[Depends(_check_module_enabled)],
)
async def get_work_session_details(
    session_id: Annotated[
        str, Path(..., description="The unique ID of the work session.")
    ],
    handler: SessionHandlerCheckedDep,
):
    logger.debug(f"Request for work session details: {session_id}")
    try:
        session_meta = await handler.get_session_metadata(session_id)
    except ValueError as ve:
        logger.warning(
            f"Get session failed: Invalid session ID format '{session_id}': {ve}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session ID format: {session_id}",
        )

    if not session_meta:
        logger.warning(f"Work session ID '{session_id}' not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work Session ID '{session_id}' not found.",
        )
    return session_meta


@router.put(
    "/{session_id}",
    response_model=SessionMetadata,
    summary="Update an Existing Work Session",
    tags=[TAG_SESSIONS],
    dependencies=[Depends(_check_module_enabled)],
)
async def update_work_session_details(
    session_id: Annotated[
        str, Path(..., description="The ID of the work session to update.")
    ],
    update_data: Annotated[SessionUpdate, Body(...)],
    handler: SessionHandlerCheckedDep,
):
    logger.info(
        f"Request to update work session: {session_id} with data: {update_data.model_dump(exclude_unset=True)}"
    )
    try:
        updated_session_meta = await handler.update_session_metadata(
            session_id, update_data
        )
    except ValueError as ve:
        logger.warning(
            f"Update session failed: Invalid session ID format '{session_id}': {ve}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session ID format: {session_id}",
        )

    if not updated_session_meta:
        logger.warning(
            f"Failed to update work session '{session_id}'. It might not exist or an error occurred."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work Session ID '{session_id}' not found or could not be updated.",
        )
    logger.info(f"Work session '{session_id}' updated successfully.")
    return updated_session_meta


@router.delete(
    "/{session_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Work Session",
    tags=[TAG_SESSIONS],
    dependencies=[Depends(_check_module_enabled)],
)
async def delete_work_session_by_id(
    session_id: Annotated[
        str, Path(..., description="The ID of the work session to delete.")
    ],
    handler: SessionHandlerCheckedDep,
):
    logger.info(f"Request to delete work session: {session_id}")
    try:
        deleted_successfully = await handler.delete_session(session_id)
        if not deleted_successfully:
            session_exists = await handler.get_session_metadata(session_id)
            if not session_exists:
                logger.warning(
                    f"Attempted to delete session '{session_id}' but it was not found (or already deleted)."
                )
                # For DELETE, if not found, it's often acceptable to return 204 or 404.
                # Here, if delete_session returns False because it wasn't found, a 404 is more accurate.
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Work Session ID '{session_id}' not found for deletion.")
            else: # It exists but delete failed
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Could not delete session '{session_id}'.",
                )
        logger.info(f"Work session '{session_id}' processed for deletion.")
        return # No return body for 204
    except ValueError as ve:
        logger.warning(
            f"Delete session failed: Invalid session ID format '{session_id}': {ve}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session ID format: {session_id}",
        )
    except IOError as ioe:
        logger.error(
            f"Delete session failed for '{session_id}' due to IOError: {ioe}",
            exc_info=True,
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(ioe))
    except Exception as e:
        logger.error(
            f"Unexpected error deleting session '{session_id}': {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


# --- Endpoints for Session AI Model Configuration ---

@router.get(
    "/{session_id}/ai_config",
    response_model=AIModelSessionConfig,
    summary="Get AI Model Configuration for a Work Session",
    tags=[TAG_SESSIONS],
    dependencies=[Depends(_check_module_enabled)],
)
async def get_session_ai_config(
    session_id: Annotated[str, Path(..., description="The unique ID of the work session.")],
    handler: SessionHandlerCheckedDep,
):
    logger.debug(f"Request for AI model config for session: {session_id}")
    try:
        from uuid import UUID
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session_id format.")

    ai_config = await handler.get_ai_model_session_config(session_uuid)
    if not ai_config:
        # Return a default or empty config if none exists, or 404 if preferred
        # For now, let's return a default AIModelSessionConfig to make client handling easier
        logger.info(f"No specific AI model config found for session {session_id}, returning default/empty.")
        return AIModelSessionConfig() # Returns a model with all fields as None or default
        # If 404 is preferred:
        # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"AI Model configuration not found for session '{session_id}'.")
    return ai_config

@router.put(
    "/{session_id}/ai_config",
    response_model=AIModelSessionConfig,
    summary="Update AI Model Configuration for a Work Session",
    tags=[TAG_SESSIONS],
    dependencies=[Depends(_check_module_enabled)],
)
async def update_session_ai_config(
    session_id: Annotated[str, Path(..., description="The ID of the work session to update AI config for.")],
    config_data: Annotated[AIModelSessionConfig, Body(...)],
    handler: SessionHandlerCheckedDep,
):
    logger.info(f"Request to update AI model config for session: {session_id} with data: {config_data.model_dump(exclude_unset=True)}")
    try:
        from uuid import UUID
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session_id format.")

    updated_config = await handler.update_ai_model_session_config(session_uuid, config_data)
    if not updated_config:
        # This could be because the session itself doesn't exist or write failed
        # Check if session exists to give a more specific error
        session_meta = await handler.get_session_metadata(session_uuid)
        if not session_meta:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Work Session ID '{session_id}' not found.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not update AI model configuration for session '{session_id}'.",
        )
    logger.info(f"AI model config for session '{session_id}' updated successfully.")
    return updated_config
