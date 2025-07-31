# AiCockpit Workspace User Guide

This guide explains how to use the containerized development environments (workspaces) in AiCockpit.

## Overview

AiCockpit provides containerized development environments that you can launch instantly. Each workspace runs in an isolated Docker container with its own file system and terminal access.

## Getting Started

### 1. Accessing Workspaces

1. Navigate to the "Workspaces" section from the main navigation bar
2. You'll see a list of your existing workspaces or a button to create a new one

### 2. Creating a New Workspace

1. Click the "Create Workspace" button
2. Fill in the workspace details:
   - **Name**: A descriptive name for your workspace
   - **Description**: Optional description of the workspace purpose
   - **Image**: Select a Docker image for your development environment:
     - Anaconda Python: Pre-configured Python environment with popular data science libraries
     - Node.js 18: JavaScript/Node.js development environment
     - Python 3.11: Clean Python 3.11 installation
     - Go 1.21: Go programming language environment
     - Java 17: Java development environment
3. Click "Create Workspace"

### 3. Managing Workspaces

After creating a workspace, you can:

- **Start/Stop**: Control the workspace container state
- **Open IDE**: Launch the web-based IDE for that workspace
- **Delete**: Remove the workspace and all its data

### 4. Using the Web-Based IDE

When you open a workspace IDE, you'll have access to:

1. **File Browser**: Navigate and manage files in your workspace
2. **Code Editor**: Edit files with syntax highlighting
3. **AI Chat**: Interact with AI assistants for coding help
4. **Terminal**: Full terminal access to the container
5. **Workspace Settings**: Configure workspace-specific options

## Features

### Containerized Environments

Each workspace runs in an isolated Docker container, ensuring:
- Security isolation between workspaces
- Consistent development environments
- Easy cleanup and reproducibility

### AI Integration

The web-based IDE includes AI assistants that can:
- Help with coding tasks
- Explain code concepts
- Debug issues
- Suggest improvements

### Terminal Access

Each workspace provides full terminal access to the container, allowing you to:
- Run development commands
- Install packages
- Execute scripts
- Use version control (Git)

## Best Practices

1. **Organize Workspaces**: Create separate workspaces for different projects
2. **Clean Up**: Delete workspaces you're no longer using to free up resources
3. **Save Work**: For important work, use version control or export your files
4. **Use Appropriate Images**: Choose the Docker image that best matches your development needs

## Troubleshooting

### Workspace Won't Start

- Check that Docker is running on the host system
- Ensure sufficient system resources (CPU, memory, disk space)
- Check the logs for error messages

### Terminal Connection Issues

- Refresh the page to reconnect
- Ensure the workspace is in "running" state
- Check browser console for WebSocket errors

### File Access Problems

- Verify you're in the correct workspace
- Check file permissions within the container
- Ensure the file path is correct

## Getting Help

For issues not covered in this guide:

1. Check the project documentation in the `docs/` folder
2. Review the application logs for error messages
3. Submit an issue on the GitHub repository