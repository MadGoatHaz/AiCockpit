# acp_backend/routers/work_sessions.py
import logging
from typing import List 
from fastapi import APIRouter, HTTPException, Body, Path, status, Depends

from acp_backend.config import settings
# Import the class and the global instance from core
from acp_backend.core.session_handler import SessionHandler 
from acp_backend.core import session_handler as global_session_handler_instance

from acp_backend.models.work_session_models import (
    WorkSession, CreateWorkSessionRequest, UpdateWorkSessionRequest
)

logger = logging.getLogger(__name__)
router = APIRouter()
MODULE_NAME = "Work Sessions Service"
TAG_SESSIONS = "Work Session Management"

# Dependency provider function for SessionHandler
def get_session_handler_dependency() -> SessionHandler:
    if not global_session_handler_instance:
        logger.critical("SessionHandler (global instance) is not available.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Work session service is not properly initialized."
        )
    return global_session_handler_instance

def _check_module_enabled():
    if not settings.ENABLE_WORK_SESSION_MODULE:
        logger.warning(f"{MODULE_NAME} is disabled in configuration.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"{MODULE_NAME} is currently disabled."
        )

@router.post(
    "/", 
    response_model=WorkSession, 
    status_code=status.HTTP_201_CREATED, 
    summary="Create a New Work Session",
    tags=[TAG_SESSIONS]
)
async def create_new_work_session(
    request: CreateWorkSessionRequest = Body(...),
    handler: SessionHandler = Depends(get_session_handler_dependency) # Use dependency
):
    _check_module_enabled()
    logger.info(f"Request to create new work session with name: '{request.name}'")
    try:
        new_session = await handler.create_session(request)
        logger.info(f"Work session '{new_session.name}' (ID: {new_session.session_id}) created successfully.")
        return new_session
    except RuntimeError as e: 
        logger.error(f"Runtime error creating work session '{request.name}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e: 
        logger.error(f"Unexpected error creating work session '{request.name}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

@router.get(
    "/", 
    response_model=List[WorkSession], 
    summary="List All Work Sessions",
    tags=[TAG_SESSIONS]
)
async def list_all_work_sessions(
    handler: SessionHandler = Depends(get_session_handler_dependency) # Use dependency
):
    _check_module_enabled()
    logger.debug("Request to list all work sessions.")
    try:
        sessions = await handler.list_sessions()
        logger.debug(f"Returning {len(sessions)} work sessions.")
        return sessions
    except IOError as e: 
        logger.error(f"I/O error listing work sessions: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list sessions due to I/O error: {str(e)}")
    except Exception as e:
        logger.error(f"Error listing work sessions: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list work sessions: {str(e)}")

@router.get(
    "/{session_id}", 
    response_model=WorkSession, 
    summary="Get Details of a Specific Work Session",
    tags=[TAG_SESSIONS]
)
async def get_work_session_details(
    session_id: str = Path(..., description="The unique ID of the work session."),
    handler: SessionHandler = Depends(get_session_handler_dependency) # Use dependency
):
    _check_module_enabled()
    logger.debug(f"Request for work session details: {session_id}")
    try:
        session = await handler.get_session(session_id)
    except ValueError as ve: 
        logger.warning(f"Get session failed: Invalid session ID format '{session_id}': {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid session ID format: {session_id}")
    
    if not session:
        logger.warning(f"Work session ID '{session_id}' not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Work Session ID '{session_id}' not found.")
    return session

@router.put(
    "/{session_id}", 
    response_model=WorkSession, 
    summary="Update an Existing Work Session",
    tags=[TAG_SESSIONS]
)
async def update_work_session_details(
    session_id: str = Path(..., description="The ID of the work session to update."),
    update_data: UpdateWorkSessionRequest = Body(...),
    handler: SessionHandler = Depends(get_session_handler_dependency) # Use dependency
):
    _check_module_enabled()
    logger.info(f"Request to update work session: {session_id} with data: {update_data.model_dump(exclude_unset=True)}")
    try:
        updated_session = await handler.update_session(session_id, update_data)
    except ValueError as ve: 
        logger.warning(f"Update session failed: Invalid session ID format '{session_id}': {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid session ID format: {session_id}")

    if not updated_session:
        logger.warning(f"Failed to update work session '{session_id}'. It might not exist or an error occurred.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Work Session ID '{session_id}' not found or could not be updated.")
    logger.info(f"Work session '{session_id}' updated successfully.")
    return updated_session

@router.delete(
    "/{session_id}", 
    response_model=None, 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Work Session",
    tags=[TAG_SESSIONS]
)
async def delete_work_session_by_id(
    session_id: str = Path(..., description="The ID of the work session to delete."),
    handler: SessionHandler = Depends(get_session_handler_dependency) # Use dependency
):
    _check_module_enabled()
    logger.info(f"Request to delete work session: {session_id}")
    try:
        deleted_successfully = await handler.delete_session(session_id)
        if not deleted_successfully: 
            logger.error(f"Failed to delete work session '{session_id}' due to an internal storage error.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not delete session '{session_id}'.")
        logger.info(f"Work session '{session_id}' processed for deletion.")
        return 
    except ValueError as ve: 
        logger.warning(f"Delete session failed: Invalid session ID format '{session_id}': {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid session ID format: {session_id}")
    except IOError as ioe: 
        logger.error(f"Delete session failed for '{session_id}': {ioe}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ioe))
    except Exception as e: 
        logger.error(f"Unexpected error deleting session '{session_id}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")
