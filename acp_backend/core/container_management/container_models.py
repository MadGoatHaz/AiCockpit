"""
Data models for container management in AiCockpit
================================================

This module defines the data models used for container management operations.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ContainerStatus(str, Enum):
    """Enumeration of possible container statuses."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    DELETED = "deleted"
    ERROR = "error"


class ContainerResourceConfig(BaseModel):
    """Configuration for container resources."""
    cpu_limit: Optional[str] = Field(default=None, description="CPU limit for the container (e.g., '1.0' for 1 CPU)")
    memory_limit: Optional[str] = Field(default=None, description="Memory limit for the container (e.g., '512m' for 512MB)")
    storage_limit: Optional[str] = Field(default=None, description="Storage limit for the container (e.g., '10g' for 10GB)")


class ContainerPortMapping(BaseModel):
    """Port mapping configuration for containers."""
    host_port: int = Field(description="Port on the host machine")
    container_port: int = Field(description="Port inside the container")
    protocol: str = Field(default="tcp", description="Protocol (tcp or udp)")


class ContainerVolumeMapping(BaseModel):
    """Volume mapping configuration for containers."""
    host_path: str = Field(description="Path on the host machine")
    container_path: str = Field(description="Path inside the container")
    read_only: bool = Field(default=False, description="Whether the volume is read-only")


class ContainerEnvironmentVar(BaseModel):
    """Environment variable for containers."""
    name: str = Field(description="Name of the environment variable")
    value: str = Field(description="Value of the environment variable")


class ContainerConfig(BaseModel):
    """Configuration for creating a container."""
    name: str = Field(description="Name of the container")
    image: str = Field(description="Docker image to use")
    command: Optional[List[str]] = Field(default=None, description="Command to run in the container")
    ports: List[ContainerPortMapping] = Field(default_factory=list, description="Port mappings")
    volumes: List[ContainerVolumeMapping] = Field(default_factory=list, description="Volume mappings")
    environment: List[ContainerEnvironmentVar] = Field(default_factory=list, description="Environment variables")
    resources: ContainerResourceConfig = Field(default_factory=ContainerResourceConfig, description="Resource limits")
    network_mode: Optional[str] = Field(default=None, description="Network mode for the container")
    working_dir: Optional[str] = Field(default=None, description="Working directory inside the container")


class ContainerInfo(BaseModel):
    """Information about a container."""
    id: str = Field(description="Unique identifier of the container")
    name: str = Field(description="Name of the container")
    image: str = Field(description="Docker image used")
    status: ContainerStatus = Field(description="Current status of the container")
    created_at: datetime = Field(description="When the container was created")
    started_at: Optional[datetime] = Field(default=None, description="When the container was started")
    ports: List[ContainerPortMapping] = Field(default_factory=list, description="Port mappings")
    volumes: List[ContainerVolumeMapping] = Field(default_factory=list, description="Volume mappings")
    resource_usage: Dict[str, Any] = Field(default_factory=dict, description="Current resource usage")


class WorkspaceConfig(BaseModel):
    """Configuration for a development workspace."""
    id: str = Field(description="Unique identifier for the workspace")
    name: str = Field(description="Name of the workspace")
    description: Optional[str] = Field(default=None, description="Description of the workspace")
    owner_id: str = Field(description="ID of the user who owns this workspace")
    container_config: ContainerConfig = Field(description="Configuration for the workspace container")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the workspace was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the workspace was last updated")


class WorkspaceInfo(BaseModel):
    """Information about a development workspace."""
    id: str = Field(description="Unique identifier for the workspace")
    name: str = Field(description="Name of the workspace")
    description: Optional[str] = Field(default=None, description="Description of the workspace")
    owner_id: str = Field(description="ID of the user who owns this workspace")
    container_info: ContainerInfo = Field(description="Information about the workspace container")
    status: ContainerStatus = Field(description="Current status of the workspace")
    created_at: datetime = Field(description="When the workspace was created")
    updated_at: datetime = Field(description="When the workspace was last updated")