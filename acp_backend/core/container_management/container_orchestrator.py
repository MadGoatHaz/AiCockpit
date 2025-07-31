"""
Container Orchestration Service for AiCockpit
============================================

This module provides the core container orchestration functionality for managing
containerized development environments.
"""

import logging
import docker
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
from pathlib import Path

from acp_backend.core.container_management.container_models import (
    ContainerConfig, ContainerInfo, ContainerStatus, WorkspaceConfig, WorkspaceInfo
)
from acp_backend.core.container_management.container_exceptions import (
    ContainerError, ContainerNotFoundError, ContainerCreationError
)

logger = logging.getLogger(__name__)


class ContainerOrchestrator:
    """Main container orchestration service."""
    
    def __init__(self, docker_socket: str = "unix://var/run/docker.sock", max_pool_size: int = 10):
        """
        Initialize the container orchestrator.
        
        Args:
            docker_socket: Path to the Docker socket
            max_pool_size: Maximum number of connections in the pool
        """
        try:
            # Create Docker client with connection pooling
            self.docker_client = docker.DockerClient(
                base_url=docker_socket,
                max_pool_size=max_pool_size
            )
            self._verify_docker_connection()
            self.docker_available = True
        except Exception as e:
            logger.warning(f"Docker not available: {e}")
            self.docker_available = False
            self.docker_client = None
    
    def is_docker_available(self) -> bool:
        """
        Check if Docker is available and working.
        
        Returns:
            True if Docker is available, False otherwise
        """
        if not self.docker_available or self.docker_client is None:
            return False
            
        try:
            self.docker_client.ping()
            return True
        except Exception as e:
            logger.warning(f"Docker not available: {e}")
            return False
        
    def _verify_docker_connection(self):
        """Verify that we can connect to the Docker daemon."""
        try:
            self.docker_client.ping()
            logger.info("Successfully connected to Docker daemon")
        except Exception as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            raise ContainerError(f"Cannot connect to Docker daemon: {e}")
    
    async def create_container(self, config: ContainerConfig) -> ContainerInfo:
        """
        Create a new container based on the provided configuration.
        
        This method handles the complete container creation process:
        1. Prepares Docker API parameters from the configuration
        2. Pulls the required Docker image if it doesn't exist locally
        3. Creates and starts the container
        4. Returns detailed information about the created container
        
        Args:
            config: Container configuration including image, ports, volumes, etc.
            
        Returns:
            ContainerInfo object with detailed information about the created container
            
        Raises:
            ContainerCreationError: If container creation fails for any reason
        """
        try:
            logger.info(f"Creating container '{config.name}' from image '{config.image}'")
            
            # Prepare Docker API parameters
            docker_params = {
                "image": config.image,
                "name": config.name,
                "environment": {env.name: env.value for env in config.environment},
                "volumes": {
                    vol.host_path: {
                        "bind": vol.container_path, 
                        "mode": "ro" if vol.read_only else "rw"
                    } for vol in config.volumes
                },
                "ports": {
                    f"{port.container_port}/{port.protocol}": port.host_port 
                    for port in config.ports
                },
                "working_dir": config.working_dir,
                "detach": True
            }
            
            # Add command if specified
            if config.command:
                docker_params["command"] = config.command
                
            # Add resource limits if specified
            if config.resources.cpu_limit or config.resources.memory_limit:
                docker_params["host_config"] = self.docker_client.api.create_host_config(
                    cpu_quota=int(float(config.resources.cpu_limit) * 100000) if config.resources.cpu_limit else None,
                    mem_limit=config.resources.memory_limit,
                )
            
            # Pull the image if it doesn't exist
            try:
                self.docker_client.images.get(config.image)
            except docker.errors.ImageNotFound:
                logger.info(f"Pulling image '{config.image}'")
                # Use asyncio.to_thread to avoid blocking the event loop
                await asyncio.to_thread(self.docker_client.images.pull, config.image)
            
            # Create and start the container
            container = self.docker_client.containers.create(**docker_params)
            
            # Start the container
            container.start()
            
            # Get container info
            container.reload()
            container_info = self._container_to_info(container, config)
            
            logger.info(f"Successfully created container '{config.name}' with ID {container_info.id}")
            return container_info
            
        except Exception as e:
            logger.error(f"Failed to create container '{config.name}': {e}")
            raise ContainerCreationError(f"Failed to create container '{config.name}': {e}")
    
    async def start_container(self, container_id: str) -> ContainerInfo:
        """
        Start a stopped container.
        
        This method starts a container that has been previously created but is not currently running.
        It reloads the container information after starting to ensure the returned status is accurate.
        
        Args:
            container_id: ID of the container to start
            
        Returns:
            ContainerInfo object with updated information about the started container
            
        Raises:
            ContainerNotFoundError: If container with the specified ID doesn't exist
            ContainerError: If there's an error starting the container
        """
        try:
            container = self.docker_client.containers.get(container_id)
            container.start()
            container.reload()
            
            # Get the original config if available
            config = self._get_container_config(container)
            container_info = self._container_to_info(container, config)
            
            logger.info(f"Successfully started container '{container_info.name}'")
            return container_info
            
        except docker.errors.NotFound:
            logger.error(f"Container '{container_id}' not found")
            raise ContainerNotFoundError(f"Container '{container_id}' not found")
        except Exception as e:
            logger.error(f"Failed to start container '{container_id}': {e}")
            raise ContainerError(f"Failed to start container '{container_id}': {e}")
    
    async def stop_container(self, container_id: str) -> ContainerInfo:
        """
        Stop a running container.
        
        This method gracefully stops a container that is currently running.
        It sends a SIGTERM signal to the container's main process, giving it time to shut down cleanly.
        If the container doesn't stop within a timeout period, a SIGKILL signal is sent to force termination.
        After stopping, it reloads the container information to ensure the returned status is accurate.
        
        Args:
            container_id: ID of the container to stop
            
        Returns:
            ContainerInfo object with updated information about the stopped container
            
        Raises:
            ContainerNotFoundError: If container with the specified ID doesn't exist
            ContainerError: If there's an error stopping the container
        """
        try:
            container = self.docker_client.containers.get(container_id)
            container.stop()
            container.reload()
            
            # Get the original config if available
            config = self._get_container_config(container)
            container_info = self._container_to_info(container, config)
            
            logger.info(f"Successfully stopped container '{container_info.name}'")
            return container_info
            
        except docker.errors.NotFound:
            logger.error(f"Container '{container_id}' not found")
            raise ContainerNotFoundError(f"Container '{container_id}' not found")
        except Exception as e:
            logger.error(f"Failed to stop container '{container_id}': {e}")
            raise ContainerError(f"Failed to stop container '{container_id}': {e}")
    
    async def delete_container(self, container_id: str, force: bool = False) -> bool:
        """
        Delete a container.
        
        This method removes a container from the system. If the container is running,
        it must be stopped first unless the force parameter is set to True.
        
        Args:
            container_id: ID of the container to delete
            force: Whether to force deletion of running containers (default: False)
            
        Returns:
            True if deletion was successful
            
        Raises:
            ContainerNotFoundError: If container with the specified ID doesn't exist
            ContainerError: If there's an error deleting the container
        """
        try:
            container = self.docker_client.containers.get(container_id)
            container.remove(force=force)
            
            logger.info(f"Successfully deleted container '{container_id}'")
            return True
            
        except docker.errors.NotFound:
            logger.error(f"Container '{container_id}' not found")
            raise ContainerNotFoundError(f"Container '{container_id}' not found")
        except Exception as e:
            logger.error(f"Failed to delete container '{container_id}': {e}")
            raise ContainerError(f"Failed to delete container '{container_id}': {e}")
    
    async def get_container_info(self, container_id: str) -> ContainerInfo:
        """
        Get detailed information about a container.
        
        This method retrieves comprehensive information about a container including its current status,
        resource usage, port mappings, and volume mappings. It's useful for monitoring container
        health and displaying container details in the UI.
        
        Args:
            container_id: ID of the container
            
        Returns:
            ContainerInfo object with detailed information about the container
            
        Raises:
            ContainerNotFoundError: If container with the specified ID doesn't exist
            ContainerError: If there's an error retrieving container information
        """
        try:
            container = self.docker_client.containers.get(container_id)
            container.reload()
            
            # Get the original config if available
            config = self._get_container_config(container)
            container_info = self._container_to_info(container, config)
            
            return container_info
            
        except docker.errors.NotFound:
            logger.error(f"Container '{container_id}' not found")
            raise ContainerNotFoundError(f"Container '{container_id}' not found")
        except Exception as e:
            logger.error(f"Failed to get info for container '{container_id}': {e}")
            raise ContainerError(f"Failed to get info for container '{container_id}': {e}")
    
    async def list_containers(self, all_containers: bool = False) -> List[ContainerInfo]:
        """
        List all containers with detailed information.
        
        This method retrieves information about all containers managed by the Docker daemon.
        By default, it only returns running containers, but can be configured to include
        stopped containers as well.
        
        Args:
            all_containers: Whether to include stopped containers (default: False)
            
        Returns:
            List of ContainerInfo objects with detailed information about each container
            
        Raises:
            ContainerError: If there's an error retrieving the container list
        """
        try:
            containers = self.docker_client.containers.list(all=all_containers)
            container_infos = []
            
            for container in containers:
                # Get the original config if available
                config = self._get_container_config(container)
                container_info = self._container_to_info(container, config)
                container_infos.append(container_info)
            
            return container_infos
            
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            raise ContainerError(f"Failed to list containers: {e}")
    
    def _container_to_info(self, container, config: Optional[ContainerConfig] = None) -> ContainerInfo:
        """
        Convert a Docker container object to ContainerInfo.
        
        Args:
            container: Docker container object
            config: Original container configuration if available
            
        Returns:
            ContainerInfo object
        """
        # Get container status
        status_map = {
            "created": ContainerStatus.CREATED,
            "running": ContainerStatus.RUNNING,
            "paused": ContainerStatus.PAUSED,
            "exited": ContainerStatus.STOPPED,
            "dead": ContainerStatus.ERROR,
            "removing": ContainerStatus.DELETED
        }
        
        container_status = status_map.get(container.status, ContainerStatus.ERROR)
        
        # Get port mappings
        ports = []
        if container.ports:
            for container_port, host_bindings in container.ports.items():
                if host_bindings:
                    for binding in host_bindings:
                        port_info = container_port.split('/')
                        ports.append({
                            "host_port": int(binding['HostPort']),
                            "container_port": int(port_info[0]),
                            "protocol": port_info[1] if len(port_info) > 1 else "tcp"
                        })
        
        # Get volume mappings
        volumes = []
        if container.attrs.get('Mounts'):
            for mount in container.attrs['Mounts']:
                volumes.append({
                    "host_path": mount.get('Source', ''),
                    "container_path": mount.get('Destination', ''),
                    "read_only": mount.get('Mode') == 'ro'
                })
        
        # Get resource usage (basic info)
        resource_usage = {}
        try:
            stats = container.stats(stream=False)
            resource_usage = {
                "cpu_usage": stats.get('cpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0),
                "memory_usage": stats.get('memory_stats', {}).get('usage', 0),
                "network_rx": stats.get('networks', {}).get('eth0', {}).get('rx_bytes', 0) if stats.get('networks') else 0,
                "network_tx": stats.get('networks', {}).get('eth0', {}).get('tx_bytes', 0) if stats.get('networks') else 0
            }
        except Exception as e:
            logger.warning(f"Failed to get resource usage for container {container.id}: {e}")
        
        return ContainerInfo(
            id=container.id,
            name=container.name.lstrip('/'),  # Remove leading slash
            image=container.image.tags[0] if container.image.tags else "unknown",
            status=container_status,
            created_at=datetime.fromtimestamp(container.attrs['Created']),
            started_at=datetime.fromtimestamp(container.attrs['State']['StartedAt']) if container.attrs['State']['StartedAt'] != '0001-01-01T00:00:00Z' else None,
            ports=ports,
            volumes=volumes,
            resource_usage=resource_usage
        )
    
    def _get_container_config(self, container) -> Optional[ContainerConfig]:
        """
        Extract container configuration from a Docker container object.
        
        Args:
            container: Docker container object
            
        Returns:
            ContainerConfig object or None if not available
        """
        try:
            # This is a simplified extraction - in a real implementation,
            # you might store the original config in labels or a database
            config = ContainerConfig(
                name=container.name.lstrip('/'),
                image=container.image.tags[0] if container.image.tags else "unknown",
                command=container.attrs.get('Config', {}).get('Cmd', []),
                ports=[],  # Would need to reconstruct from container.ports
                volumes=[],  # Would need to reconstruct from container.attrs['Mounts']
                environment=[],  # Would need to reconstruct from container.attrs['Config']['Env']
                resources=ContainerResourceConfig()
            )
            return config
        except Exception as e:
            logger.warning(f"Failed to extract config from container {container.id}: {e}")
            return None
    
    async def create_workspace(self, workspace_config: WorkspaceConfig) -> WorkspaceInfo:
        """
        Create a new development workspace.
        
        This method creates a complete development workspace by setting up a container
        with the specified configuration. The workspace includes:
        - A container running the specified development environment
        - Configured port mappings for development tools
        - Volume mappings for persistent storage
        - Environment variables for workspace identification
        
        Args:
            workspace_config: Configuration for the workspace including container settings
            
        Returns:
            WorkspaceInfo object with detailed information about the created workspace
            
        Raises:
            ContainerCreationError: If workspace container creation fails
        """
        try:
            logger.info(f"Creating workspace '{workspace_config.name}' for user '{workspace_config.owner_id}'")
            
            # Create the container for the workspace
            container_info = await self.create_container(workspace_config.container_config)
            
            # Create workspace info
            workspace_info = WorkspaceInfo(
                id=workspace_config.id,
                name=workspace_config.name,
                description=workspace_config.description,
                owner_id=workspace_config.owner_id,
                container_info=container_info,
                status=container_info.status,
                created_at=workspace_config.created_at,
                updated_at=workspace_config.updated_at
            )
            
            logger.info(f"Successfully created workspace '{workspace_config.name}' with container ID {container_info.id}")
            return workspace_info
            
        except Exception as e:
            logger.error(f"Failed to create workspace '{workspace_config.name}': {e}")
            raise ContainerCreationError(f"Failed to create workspace '{workspace_config.name}': {e}")
    
    async def cleanup_orphaned_containers(self) -> int:
        """
        Clean up orphaned containers that are not associated with any workspace.
        
        This method identifies and removes containers that are no longer associated
        with any active workspace. This helps prevent resource leaks and keeps the
        system clean. In a production environment, this method would check against
        a database of active workspaces to determine which containers are orphaned.
        
        Returns:
            Number of containers cleaned up
            
        Raises:
            ContainerError: If there's an error during cleanup
        """
        try:
            # In a real implementation, you would check against your workspace database
            # For now, we'll just log that this method exists
            logger.info("Cleaning up orphaned containers")
            cleaned_count = 0
            
            # This is a placeholder - in a real implementation you would:
            # 1. Get list of all containers
            # 2. Check which ones are associated with active workspaces
            # 3. Stop and remove orphaned containers
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to clean up orphaned containers: {e}")
            raise ContainerError(f"Failed to clean up orphaned containers: {e}")