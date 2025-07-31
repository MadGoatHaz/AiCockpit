"""
Custom exceptions for container management in AiCockpit
=====================================================

This module defines custom exceptions used throughout the container management system.
"""

class ContainerError(Exception):
    """Base exception for container-related errors."""
    pass


class ContainerNotFoundError(ContainerError):
    """Raised when a container cannot be found."""
    pass


class ContainerCreationError(ContainerError):
    """Raised when container creation fails."""
    pass


class ContainerStartError(ContainerError):
    """Raised when container start fails."""
    pass


class ContainerStopError(ContainerError):
    """Raised when container stop fails."""
    pass


class ContainerDeleteError(ContainerError):
    """Raised when container deletion fails."""
    pass


class WorkspaceError(ContainerError):
    """Base exception for workspace-related errors."""
    pass


class WorkspaceNotFoundError(WorkspaceError):
    """Raised when a workspace cannot be found."""
    pass


class WorkspaceCreationError(WorkspaceError):
    """Raised when workspace creation fails."""
    pass