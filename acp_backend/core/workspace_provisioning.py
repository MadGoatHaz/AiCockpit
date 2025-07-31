"""
Workspace Provisioning Service for AiCockpit
===========================================

This module provides the workspace provisioning functionality for creating and
managing complete development environments.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio
import uuid
from datetime import datetime

from acp_backend.core.container_management.container_orchestrator import ContainerOrchestrator
from acp_backend.core.container_management.container_models import (
    WorkspaceConfig, ContainerConfig, ContainerResourceConfig,
    ContainerPortMapping, ContainerVolumeMapping, ContainerEnvironmentVar
)
from acp_backend.core.container_management.container_exceptions import (
    WorkspaceCreationError, ContainerCreationError
)

logger = logging.getLogger(__name__)


class WorkspaceProvisioningService:
    """Service for provisioning complete development workspaces."""
    
    def __init__(self, 
                 container_orchestrator: ContainerOrchestrator,
                 base_storage_path: str = "/var/lib/ai-cockpit/workspaces",
                 base_image: str = "continuumio/anaconda3"):
        """
        Initialize the workspace provisioning service.
        
        Args:
            container_orchestrator: Container orchestrator instance
            base_storage_path: Base path for workspace storage
            base_image: Default Docker image for workspaces
        """
        self.container_orchestrator = container_orchestrator
        self.base_storage_path = Path(base_storage_path)
        self.base_image = base_image
        
        # Ensure base storage path exists
        try:
            self.base_storage_path.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Use a user-writable path instead
            self.base_storage_path = Path.home() / ".acp" / "workspaces"
            self.base_storage_path.mkdir(parents=True, exist_ok=True)
        
    async def provision_workspace(self,
                                 name: str,
                                 owner_id: str,
                                 description: Optional[str] = None,
                                 image: Optional[str] = None,
                                 cpu_limit: Optional[str] = None,
                                 memory_limit: Optional[str] = None,
                                 storage_limit: Optional[str] = None,
                                 initial_files: Optional[Dict[str, str]] = None,
                                 environment_vars: Optional[Dict[str, str]] = None) -> str:
        """
        Provision a new development workspace.
        
        This method creates a complete development workspace including:
        - A dedicated storage directory for workspace files
        - A container running the specified development environment
        - Configured resource limits (CPU, memory)
        - Initial files and environment variables
        
        The provisioning process involves several steps:
        1. Creating a unique workspace ID
        2. Setting up workspace storage directory
        3. Initializing with any provided initial files
        4. Creating container configuration with appropriate mappings
        5. Creating and starting the workspace container
        
        Args:
            name: Name of the workspace
            owner_id: ID of the user who owns this workspace
            description: Description of the workspace
            image: Docker image to use (defaults to base_image)
            cpu_limit: CPU limit for the container (e.g., '1.0' for 1 CPU)
            memory_limit: Memory limit for the container (e.g., '512m' for 512MB)
            storage_limit: Storage limit for the container (e.g., '10g' for 10GB)
            initial_files: Dictionary of filename -> content for initial files
            environment_vars: Dictionary of environment variables
            
        Returns:
            ID of the provisioned workspace
            
        Raises:
            WorkspaceCreationError: If workspace provisioning fails
        """
        try:
            logger.info(f"Provisioning workspace '{name}' for user '{owner_id}'")
            
            # Generate a unique workspace ID
            workspace_id = str(uuid.uuid4())
            
            # Create workspace storage directory
            workspace_storage_path = self._create_workspace_storage(workspace_id)
            
            # Initialize with initial files if provided
            if initial_files:
                await self._initialize_workspace_files(workspace_storage_path, initial_files)
            
            # Create container configuration
            container_config = self._create_container_config(
                workspace_id=workspace_id,
                workspace_storage_path=workspace_storage_path,
                image=image or self.base_image,
                cpu_limit=cpu_limit,
                memory_limit=memory_limit,
                storage_limit=storage_limit,
                environment_vars=environment_vars
            )
            
            # Create workspace configuration
            workspace_config = WorkspaceConfig(
                id=workspace_id,
                name=name,
                description=description,
                owner_id=owner_id,
                container_config=container_config
            )
            
            # Create the workspace container
            workspace_info = await self.container_orchestrator.create_workspace(workspace_config)
            
            logger.info(f"Successfully provisioned workspace '{name}' with ID {workspace_id}")
            return workspace_id
            
        except WorkspaceCreationError:
            # Re-raise workspace creation errors as-is
            raise
        except Exception as e:
            logger.error(f"Failed to provision workspace '{name}': {e}")
            raise WorkspaceCreationError(f"Failed to provision workspace '{name}': {str(e)}")
    
    def _create_workspace_storage(self, workspace_id: str) -> Path:
        """
        Create storage directory for a workspace.
        
        Args:
            workspace_id: ID of the workspace
            
        Returns:
            Path to the workspace storage directory
        """
        workspace_storage_path = self.base_storage_path / workspace_id
        workspace_storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created storage directory for workspace {workspace_id} at {workspace_storage_path}")
        return workspace_storage_path
    
    async def _initialize_workspace_files(self, storage_path: Path, files: Dict[str, str]):
        """
        Initialize workspace with initial files.
        
        Args:
            storage_path: Path to workspace storage
            files: Dictionary of filename -> content
        """
        for filename, content in files.items():
            file_path = storage_path / filename
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            # Write file content
            file_path.write_text(content)
            logger.info(f"Created initial file {filename} in workspace")
    
    def _create_container_config(self,
                                workspace_id: str,
                                workspace_storage_path: Path,
                                image: str,
                                cpu_limit: Optional[str] = None,
                                memory_limit: Optional[str] = None,
                                storage_limit: Optional[str] = None,
                                environment_vars: Optional[Dict[str, str]] = None) -> ContainerConfig:
        """
        Create container configuration for a workspace.
        
        Args:
            workspace_id: ID of the workspace
            workspace_storage_path: Path to workspace storage
            image: Docker image to use
            cpu_limit: CPU limit for the container
            memory_limit: Memory limit for the container
            storage_limit: Storage limit for the container
            environment_vars: Environment variables
            
        Returns:
            Container configuration
        """
        # Default ports for development tools
        ports = [
            ContainerPortMapping(host_port=8080, container_port=8080, protocol="tcp"),  # VS Code server
            ContainerPortMapping(host_port=8081, container_port=8081, protocol="tcp"),  # Additional services
        ]
        
        # Volume mappings
        volumes = [
            ContainerVolumeMapping(
                host_path=str(workspace_storage_path),
                container_path="/workspace",
                read_only=False
            )
        ]
        
        # Environment variables
        env_vars = [
            ContainerEnvironmentVar(name="WORKSPACE_ID", value=workspace_id),
            ContainerEnvironmentVar(name="WORKSPACE_NAME", value=f"workspace-{workspace_id}"),
        ]
        
        # Add custom environment variables
        if environment_vars:
            for name, value in environment_vars.items():
                env_vars.append(ContainerEnvironmentVar(name=name, value=value))
        
        # Resource configuration
        resources = ContainerResourceConfig(
            cpu_limit=cpu_limit,
            memory_limit=memory_limit,
            storage_limit=storage_limit
        )
        
        return ContainerConfig(
            name=f"workspace-{workspace_id}",
            image=image,
            ports=ports,
            volumes=volumes,
            environment=env_vars,
            resources=resources,
            working_dir="/workspace"
        )
    
    async def deprovision_workspace(self, workspace_id: str, force: bool = False) -> bool:
        """
        Deprovision a workspace, removing both container and storage.
        
        This method cleanly removes a workspace by:
        1. Stopping and removing the associated container
        2. Deleting the workspace storage directory and all its contents
        
        This is a destructive operation that cannot be undone. All files and data
        associated with the workspace will be permanently deleted.
        
        Args:
            workspace_id: ID of the workspace to deprovision
            force: Whether to force removal of running containers (default: False)
            
        Returns:
            True if deprovisioning was successful
            
        Raises:
            WorkspaceCreationError: If workspace deprovisioning fails
        """
        try:
            logger.info(f"Deprovisioning workspace {workspace_id}")
            
            # Stop and remove the container
            container_name = f"workspace-{workspace_id}"
            try:
                await self.container_orchestrator.delete_container(container_name, force=force)
            except Exception as e:
                logger.warning(f"Failed to delete container for workspace {workspace_id}: {e}")
                if not force:
                    raise
            
            # Remove workspace storage
            workspace_storage_path = self.base_storage_path / workspace_id
            if workspace_storage_path.exists():
                shutil.rmtree(workspace_storage_path)
                logger.info(f"Removed storage directory for workspace {workspace_id}")
            
            logger.info(f"Successfully deprovisioned workspace {workspace_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deprovision workspace {workspace_id}: {e}")
            raise WorkspaceCreationError(f"Failed to deprovision workspace {workspace_id}: {e}")
    
    async def get_workspace_info(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a workspace.
        
        This method retrieves detailed information about a workspace including:
        - Container information (status, resource usage, ports, etc.)
        - Storage information (path, size, limits)
        - Workspace metadata (ID, name, description, owner)
        
        This information is useful for displaying workspace details in the UI
        and for monitoring workspace health and resource usage.
        
        Args:
            workspace_id: ID of the workspace
            
        Returns:
            Dictionary with comprehensive workspace information
            
        Raises:
            Exception: If there's an error retrieving workspace information
        """
        try:
            # Get container info
            container_name = f"workspace-{workspace_id}"
            container_info = await self.container_orchestrator.get_container_info(container_name)
            
            # Get storage info
            workspace_storage_path = self.base_storage_path / workspace_id
            storage_size = self._get_directory_size(workspace_storage_path) if workspace_storage_path.exists() else 0
            
            return {
                "workspace_id": workspace_id,
                "container_info": container_info.dict(),
                "storage_path": str(workspace_storage_path),
                "storage_size": storage_size,
                "storage_limit": "unlimited"  # In a real implementation, this would come from config
            }
            
        except Exception as e:
            logger.error(f"Failed to get info for workspace {workspace_id}: {e}")
            raise
    
    def _get_directory_size(self, path: Path) -> int:
        """
        Get the total size of a directory in bytes.
        
        Args:
            path: Path to directory
            
        Returns:
            Size in bytes
        """
        total_size = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception as e:
            logger.warning(f"Failed to calculate directory size for {path}: {e}")
        return total_size
    
    async def list_workspaces(self) -> Dict[str, Dict[str, Any]]:
        """
        List all provisioned workspaces with their information.
        
        This method retrieves information about all workspaces that have been provisioned,
        including both running and stopped workspaces. For each workspace, it provides:
        - Container information (status, resource usage, ports, etc.)
        - Storage information (path, size)
        - Workspace metadata (ID, name, owner)
        
        This method is useful for displaying a dashboard of all workspaces in the UI
        and for administrative tasks like cleanup of orphaned workspaces.
        
        Returns:
            Dictionary mapping workspace IDs to their comprehensive information
            
        Raises:
            Exception: If there's an error retrieving the workspace list
        """
        try:
            # Get all containers
            all_containers = await self.container_orchestrator.list_containers(all_containers=True)
            
            # Filter for workspace containers
            workspace_containers = [
                container for container in all_containers 
                if container.name.startswith("workspace-")
            ]
            
            # Build workspace info dictionary
            workspaces_info = {}
            for container in workspace_containers:
                # Extract workspace ID from container name
                if container.name.startswith("workspace-"):
                    workspace_id = container.name[len("workspace-"):]
                    
                    # Get storage info
                    workspace_storage_path = self.base_storage_path / workspace_id
                    storage_size = self._get_directory_size(workspace_storage_path) if workspace_storage_path.exists() else 0
                    
                    workspaces_info[workspace_id] = {
                        "workspace_id": workspace_id,
                        "container_info": container.dict(),
                        "storage_path": str(workspace_storage_path),
                        "storage_size": storage_size
                    }
            
            return workspaces_info
            
        except Exception as e:
            logger.error(f"Failed to list workspaces: {e}")
            raise