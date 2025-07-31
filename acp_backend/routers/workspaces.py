"""
Workspace management router for AiCockpit
========================================

This module provides API endpoints for managing development workspaces.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from datetime import datetime

from acp_backend.core.container_management.container_models import (
    WorkspaceConfig, WorkspaceInfo, ContainerConfig, ContainerResourceConfig,
    ContainerPortMapping, ContainerVolumeMapping, ContainerEnvironmentVar
)
from acp_backend.core.container_management.container_orchestrator import ContainerOrchestrator
from acp_backend.core.container_management.container_exceptions import (
    WorkspaceNotFoundError, WorkspaceCreationError, ContainerNotFoundError
)
from acp_backend.core.workspace_provisioning import WorkspaceProvisioningService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

# In a real implementation, this would be a dependency injected from the app
# For now, we'll create global instances
container_orchestrator = ContainerOrchestrator()
workspace_provisioning_service = WorkspaceProvisioningService(container_orchestrator)


class CreateWorkspaceRequest(BaseModel):
    """Request model for creating a new workspace."""
    name: str = Field(description="Name of the workspace")
    description: Optional[str] = Field(default=None, description="Description of the workspace")
    image: str = Field(default="continuumio/anaconda3", description="Docker image to use for the workspace")
    cpu_limit: Optional[str] = Field(default=None, description="CPU limit for the container (e.g., '1.0' for 1 CPU)")
    memory_limit: Optional[str] = Field(default=None, description="Memory limit for the container (e.g., '512m' for 512MB)")
    storage_limit: Optional[str] = Field(default=None, description="Storage limit for the container (e.g., '10g' for 10GB)")


class WorkspaceResponse(BaseModel):
    """Response model for workspace information."""
    id: str = Field(description="Unique identifier for the workspace")
    name: str = Field(description="Name of the workspace")
    description: Optional[str] = Field(default=None, description="Description of the workspace")
    owner_id: str = Field(description="ID of the user who owns this workspace")
    container_id: str = Field(description="ID of the container running this workspace")
    container_image: str = Field(description="Docker image used for this workspace")
    status: str = Field(description="Current status of the workspace")
    created_at: datetime = Field(description="When the workspace was created")
    updated_at: datetime = Field(description="When the workspace was last updated")


def _workspace_info_to_response(workspace_info: WorkspaceInfo, owner_id: str = "default") -> WorkspaceResponse:
    """Convert WorkspaceInfo to WorkspaceResponse."""
    return WorkspaceResponse(
        id=workspace_info.id,
        name=workspace_info.name,
        description=workspace_info.description,
        owner_id=owner_id,  # In a real implementation, this would come from auth
        container_id=workspace_info.container_info.id,
        container_image=workspace_info.container_info.image,
        status=workspace_info.container_info.status.value,
        created_at=workspace_info.created_at,
        updated_at=workspace_info.updated_at
    )


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(request: CreateWorkspaceRequest):
    """
    Create a new development workspace.
    
    This endpoint provisions a complete development workspace including:
    - A container running the specified development environment
    - A dedicated storage directory for workspace files
    - Configured resource limits (CPU, memory)
    
    The workspace will be ready to use immediately after creation, with VS Code
    server running and accessible through the web interface.
    
    Args:
        request: Workspace creation request containing name, description, image, and resource limits
        
    Returns:
        WorkspaceResponse with information about the created workspace
        
    Raises:
        HTTPException: If workspace creation fails or Docker is not available
    """
    try:
        logger.info(f"Creating workspace '{request.name}'")
        
        # Check if Docker is available
        if not container_orchestrator.is_docker_available():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Docker is not available")
        
        # Provision the workspace using the provisioning service
        workspace_id = await workspace_provisioning_service.provision_workspace(
            name=request.name,
            owner_id="default",  # In a real implementation, this would come from auth
            description=request.description,
            image=request.image,
            cpu_limit=request.cpu_limit,
            memory_limit=request.memory_limit,
            storage_limit=request.storage_limit
        )
        
        # Get workspace info
        workspace_info = await workspace_provisioning_service.get_workspace_info(workspace_id)
        
        # Create a minimal WorkspaceInfo for response
        from acp_backend.core.container_management.container_models import ContainerInfo, ContainerStatus
        container_info = ContainerInfo(
            id=workspace_info["container_info"]["id"],
            name=workspace_info["container_info"]["name"],
            image=workspace_info["container_info"]["image"],
            status=ContainerStatus(workspace_info["container_info"]["status"]),
            created_at=datetime.fromisoformat(workspace_info["container_info"]["created_at"]),
            started_at=datetime.fromisoformat(workspace_info["container_info"]["started_at"]) if workspace_info["container_info"]["started_at"] else None,
            ports=[],
            volumes=[],
            resource_usage={}
        )
        
        workspace_info_obj = WorkspaceInfo(
            id=workspace_id,
            name=request.name,
            description=request.description,
            owner_id="default",
            container_info=container_info,
            status=container_info.status,
            created_at=container_info.created_at,
            updated_at=container_info.created_at
        )
        
        # Convert to response format
        response = _workspace_info_to_response(workspace_info_obj)
        
        logger.info(f"Successfully created workspace '{request.name}' with ID {workspace_id}")
        return response
        
    except WorkspaceCreationError as e:
        logger.error(f"Failed to create workspace '{request.name}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create workspace: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error creating workspace '{request.name}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace_id: str):
    """
    Get detailed information about a specific workspace.
    
    This endpoint retrieves comprehensive information about a workspace including:
    - Current status (running, stopped, etc.)
    - Container information (ID, image, resource usage)
    - Storage information (path, size)
    - Metadata (name, description, owner)
    
    This information is useful for displaying workspace details in the UI and
    for monitoring workspace health and resource usage.
    
    Args:
        workspace_id: ID of the workspace to retrieve
        
    Returns:
        WorkspaceResponse with detailed information about the workspace
        
    Raises:
        HTTPException: If workspace is not found or Docker is not available
    """
    try:
        logger.info(f"Retrieving workspace '{workspace_id}'")
        
        # Check if Docker is available
        if not container_orchestrator.is_docker_available():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Docker is not available")
        
        # Get workspace info from the provisioning service
        workspace_info = await workspace_provisioning_service.get_workspace_info(workspace_id)
        
        if workspace_info is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workspace '{workspace_id}' not found")
        
        # Create a minimal WorkspaceInfo from the workspace data
        from acp_backend.core.container_management.container_models import ContainerInfo, ContainerStatus
        container_info_data = workspace_info["container_info"]
        container_info = ContainerInfo(
            id=container_info_data["id"],
            name=container_info_data["name"],
            image=container_info_data["image"],
            status=ContainerStatus(container_info_data["status"]),
            created_at=datetime.fromisoformat(container_info_data["created_at"]),
            started_at=datetime.fromisoformat(container_info_data["started_at"]) if container_info_data["started_at"] else None,
            ports=[],
            volumes=[],
            resource_usage={}
        )
        
        workspace_info_obj = WorkspaceInfo(
            id=workspace_id,
            name=f"Workspace {workspace_id[:8]}",
            description=workspace_info.get("description", "Auto-generated workspace"),
            owner_id=workspace_info.get("owner_id", "default"),
            container_info=container_info,
            status=container_info.status,
            created_at=container_info.created_at,
            updated_at=container_info.created_at
        )
        
        response = _workspace_info_to_response(workspace_info_obj)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving workspace '{workspace_id}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")


@router.get("/", response_model=List[WorkspaceResponse])
async def list_workspaces():
    """
    List all provisioned workspaces with their information.
    
    This endpoint retrieves information about all workspaces that have been provisioned,
    including both running and stopped workspaces. For each workspace, it provides:
    - Current status (running, stopped, etc.)
    - Container information (ID, image)
    - Metadata (name, description, owner)
    
    This endpoint is useful for displaying a dashboard of all workspaces in the UI
    and for administrative tasks like cleanup of orphaned workspaces.
    
    Returns:
        List of WorkspaceResponse objects with information about each workspace
        
    Raises:
        HTTPException: If Docker is not available or there's an internal server error
    """
    try:
        logger.info("Listing all workspaces")
        
        # Check if Docker is available
        if not container_orchestrator.is_docker_available():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Docker is not available")
        
        # Get all workspaces from the provisioning service
        workspaces_info = await workspace_provisioning_service.list_workspaces()
        
        # Convert to workspace responses
        workspace_responses = []
        for workspace_id, workspace_data in workspaces_info.items():
            # Create a minimal WorkspaceInfo from the workspace data
            from acp_backend.core.container_management.container_models import ContainerInfo, ContainerStatus
            container_info_data = workspace_data["container_info"]
            container_info = ContainerInfo(
                id=container_info_data["id"],
                name=container_info_data["name"],
                image=container_info_data["image"],
                status=ContainerStatus(container_info_data["status"]),
                created_at=datetime.fromisoformat(container_info_data["created_at"]),
                started_at=datetime.fromisoformat(container_info_data["started_at"]) if container_info_data["started_at"] else None,
                ports=[],
                volumes=[],
                resource_usage={}
            )
            
            workspace_info = WorkspaceInfo(
                id=workspace_id,
                name=f"Workspace {workspace_id[:8]}",
                description="Auto-generated workspace",
                owner_id="default",
                container_info=container_info,
                status=container_info.status,
                created_at=container_info.created_at,
                updated_at=container_info.created_at
            )
            
            response = _workspace_info_to_response(workspace_info)
            workspace_responses.append(response)
        
        return workspace_responses
        
    except Exception as e:
        logger.error(f"Unexpected error listing workspaces: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(workspace_id: str):
    """
    Delete a workspace and all associated resources.
    
    This endpoint permanently removes a workspace by:
    1. Stopping and removing the associated container
    2. Deleting the workspace storage directory and all its contents
    
    This is a destructive operation that cannot be undone. All files and data
    associated with the workspace will be permanently deleted.
    
    Args:
        workspace_id: ID of the workspace to delete
        
    Raises:
        HTTPException: If workspace is not found or there's an internal server error
    """
    try:
        logger.info(f"Deleting workspace '{workspace_id}'")
        
        # Deprovision the workspace using the provisioning service
        await workspace_provisioning_service.deprovision_workspace(workspace_id, force=True)
        
        logger.info(f"Successfully deleted workspace '{workspace_id}'")
        
    except ContainerNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workspace '{workspace_id}' not found")
    except Exception as e:
        logger.error(f"Unexpected error deleting workspace '{workspace_id}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")


@router.post("/{workspace_id}/start", response_model=WorkspaceResponse)
async def start_workspace(workspace_id: str):
    """
    Start a stopped workspace.
    
    This endpoint starts a workspace container that has been previously created
    but is not currently running. After starting, the workspace will be accessible
    through the web interface.
    
    Args:
        workspace_id: ID of the workspace to start
        
    Returns:
        WorkspaceResponse with updated information about the started workspace
        
    Raises:
        HTTPException: If workspace is not found, Docker is not available, or there's an internal server error
    """
    try:
        logger.info(f"Starting workspace '{workspace_id}'")
        
        # Check if Docker is available
        if not container_orchestrator.is_docker_available():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Docker is not available")
        
        # Get the container name for this workspace
        container_name = f"workspace-{workspace_id}"
        
        # Start the container
        container_info = await container_orchestrator.start_container(container_name)
        
        # Create a WorkspaceInfo from the container info
        workspace_info = WorkspaceInfo(
            id=workspace_id,
            name=f"Workspace {workspace_id[:8]}",
            description="Auto-generated workspace",
            owner_id="default",
            container_info=container_info,
            status=container_info.status,
            created_at=container_info.created_at,
            updated_at=datetime.utcnow()
        )
        
        response = _workspace_info_to_response(workspace_info)
        return response
        
    except ContainerNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workspace '{workspace_id}' not found")
    except Exception as e:
        logger.error(f"Unexpected error starting workspace '{workspace_id}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")


@router.post("/{workspace_id}/stop", response_model=WorkspaceResponse)
async def stop_workspace(workspace_id: str):
    """
    Stop a running workspace.
    
    This endpoint gracefully stops a workspace container that is currently running.
    The container will be shut down cleanly, preserving all data in the workspace
    storage directory. The workspace can be started again later using the start endpoint.
    
    Args:
        workspace_id: ID of the workspace to stop
        
    Returns:
        WorkspaceResponse with updated information about the stopped workspace
        
    Raises:
        HTTPException: If workspace is not found, Docker is not available, or there's an internal server error
    """
    try:
        logger.info(f"Stopping workspace '{workspace_id}'")
        
        # Check if Docker is available
        if not container_orchestrator.is_docker_available():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Docker is not available")
        
        # Get the container name for this workspace
        container_name = f"workspace-{workspace_id}"
        
        # Stop the container
        container_info = await container_orchestrator.stop_container(container_name)
        
        # Create a WorkspaceInfo from the container info
        workspace_info = WorkspaceInfo(
            id=workspace_id,
            name=f"Workspace {workspace_id[:8]}",
            description="Auto-generated workspace",
            owner_id="default",
            container_info=container_info,
            status=container_info.status,
            created_at=container_info.created_at,
            updated_at=datetime.utcnow()
        )
        
        response = _workspace_info_to_response(workspace_info)
        return response
        
    except ContainerNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workspace '{workspace_id}' not found")
    except Exception as e:
        logger.error(f"Unexpected error stopping workspace '{workspace_id}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")