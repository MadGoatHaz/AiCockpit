
---

## AiCockpit Handoff Document

**Date:** May 26, 2025
**Version:** 0.1.0-alpha (reflecting current backend state)

This document provides a comprehensive overview of the AiCockpit project, its current state, and the envisioned path forward for development. It is intended for developers joining the project or for the original developer to resume work.

---

### 1. Project Overview & Vision

*   **Name:** AiCockpit Backend (ACP)
*   **Purpose:** AiCockpit aims to be a locally hosted backend API, forming the core of an AI-driven workspace. It's designed to enable sophisticated Large Language Model (LLM) management, versatile AI agent execution, and persistent, organized work session management.
*   **Ultimate Vision:** The project aspires to deliver a self-hosted web application, reminiscent of platforms like Google's Gemini, featuring a dynamic "canvas" for file and project interaction alongside a dedicated AI chat interface. This system will empower users to run their chosen GGUF (GPT-Generated Unified Format) models on local DIY hardware (initially targeting Linux/Ubuntu environments). Access will be facilitated via a standard web browser on the local network, providing a comprehensive, integrated AI workspace. A key long-term goal is for AiCockpit to become sufficiently advanced to assist in its own ongoing development.
*   **Open Source Goal:** AiCockpit is intended to be an open-source project, shared on GitHub under the MIT license. This approach aims to encourage community involvement, contributions, and broad adoption.

---

### 2. Current Project State (Backend Focus)

*   **Architecture:** The foundation of AiCockpit is a Python (version 3.10 and newer) backend built with the FastAPI framework. PDM (Python Development Master) is utilized for robust dependency management and project tooling. A significant architectural principle is the use of a dependency injection pattern for core services, enhancing modularity and testability.
*   **Key Implemented Features:**
    *   **LLM Management:** The backend supports discovery of available GGUF models, loading models into memory (primarily via `llama-cpp-python`), unloading models, and direct interaction for chat completions. (See `acp_backend/routers/llm_service.py`).
    *   **Agent Orchestration:** Functionality exists for configuring and executing AI agents. This includes support for both globally defined agent templates and session-specific (local) agent configurations. The integration with `smolagents` for the actual execution logic is currently a placeholder and requires full implementation. (See `acp_backend/routers/agents.py` and `acp_backend/core/agent_executor.py`).
    *   **Work Session Management:** Users can create, list, retrieve metadata for, update, and delete distinct work sessions, allowing for organized, persistent project contexts. (See `acp_backend/routers/work_sessions.py`).
    *   **Work Board (File System Access):** The API provides endpoints for file and directory operations (list, read, write, delete, move, create directory) within the dedicated data storage of each work session. (See `acp_backend/routers/work_board.py`).
    *   **System Health & Configuration API:** Endpoints are available to check system status, module enablement, and view the loaded application configuration. (See `acp_backend/routers/system.py`).
    *   **Streaming SSE:** Server-Sent Events are implemented and tested for real-time streaming of LLM chat completions and agent outputs.
*   **Frontend:** Currently, no dedicated frontend web interface exists. The development of a user-friendly UI is the next major phase for the project.
*   **Stability:** The backend is considered stable and robust, particularly after recent efforts to improve test coverage, refine the dependency injection mechanism, and ensure correct SSE streaming behavior.

---

### 3. Technical Stack

*   **Programming Language:** Python 3.10+
*   **Web Framework:** FastAPI
*   **ASGI Server:** Uvicorn
*   **Dependency Management & Build System:** PDM
*   **Data Validation & Settings:** Pydantic (v2), Pydantic-Settings (for environment variable and `.env` file management)
*   **LLM Integration:**
    *   `llama-cpp-python`: Primary library for loading and interacting with GGUF-formatted LLMs locally.
    *   `smolagents`: Chosen agent framework; current integration primarily involves configuration management, with execution logic being a placeholder.
*   **Asynchronous I/O:** `asyncio` (core Python), `anyio` (ASGI compatibility), `httpx` (for testing and potential future outbound API calls), `aiofiles` (for asynchronous file operations).
*   **Streaming:** `sse-starlette` (for Server-Sent Events).
*   **Testing:** `pytest`, `pytest-asyncio`, `pytest-mock`.
*   **Linting & Formatting:** `Ruff` (for linting), `Black` (for code formatting).
*   **Environment Configuration:** `.env` files parsed by `pydantic-settings`.

---

### 4. Core Backend Components & Code Structure

The backend is organized into several key directories and modules:

*   `acp_backend/main.py`: The main entry point for the FastAPI application. It initializes the app, sets up logging, manages the application lifecycle (startup/shutdown events for initializing services), and conditionally includes API routers based on configuration.
*   `acp_backend/config.py`: Defines application settings using Pydantic's `BaseSettings`. Loads configuration from environment variables and `.env` files. It also defines and creates necessary base directories (e.g., for models, work sessions) upon import.
*   `acp_backend/dependencies.py`: Implements FastAPI's dependency injection system. This module provides functions that instantiate and return singleton instances of core services (handlers and managers), ensuring they are consistently available throughout the application and easily mockable for tests.
*   `acp_backend/core/`: Contains the core business logic of the application:
    *   `llm_manager.py`: Manages loading, unloading, and interacting with LLMs.
    *   `agent_executor.py`: Handles the execution flow for AI agents (currently placeholder for `smolagents` logic).
    *   `agent_config_handler.py`: Manages CRUD operations for global and local agent configurations.
    *   `session_handler.py`: Manages CRUD operations for work sessions, including their on-disk representation.
    *   `fs_manager.py`: Provides an abstraction layer for file system operations within work session data directories, ensuring path safety.
*   `acp_backend/routers/`: Contains FastAPI `APIRouter` modules, defining the API endpoints for different services:
    *   `system.py`: System status, ping, configuration viewing.
    *   `llm_service.py`: LLM discovery, loading, chat completions.
    *   `agents.py`: Agent configuration (global and local) and execution (streaming and non-streaming).
    *   `work_sessions.py`: Work session CRUD operations.
    *   `work_board.py`: File system operations within sessions.
*   `acp_backend/models/`: Defines Pydantic models used for API request and response validation, as well as internal data structures.
*   `work_sessions/` (Typically located at `~/.acp/work_sessions` or `ACP_BASE_DIR/work_sessions`):
    *   `_agent_configs/`: Stores JSON files for globally defined agent configurations.
    *   `<session_id>/`: Each work session has its own directory, named by its UUID.
        *   `_agents/`: Stores JSON files for agent configurations local to this session.
        *   `data/`: The primary data storage area for files and artifacts related to this session.
        *   `session_manifest.json`: Contains metadata about the work session (name, description, timestamps).

---

### 5. Development Environment Setup

1.  **Prerequisites:**
    *   Python 3.10 or newer.
    *   PDM (Python Development Master): Follow installation instructions at [pdm-project.org](https://pdm-project.org/).
2.  **Clone the Repository:**
    ```bash
    git clone <your_repository_url>
    cd aicockpit
    ```
3.  **Install Dependencies:**
    *   Install main and development dependencies using PDM:
        ```bash
        pdm install -G dev
        ```
        This creates a local `.venv` in the project directory and installs all necessary packages.
4.  **Configuration:**
    *   Copy the example environment file:
        ```bash
        cp example.env .env
        ```
    *   Edit the `.env` file in the project root. Key variables to review/set:
        *   `ACP_BASE_DIR`: The root directory where AiCockpit stores its data (models, sessions, logs). Defaults to `~/.acp`.
        *   `MODELS_DIR`: Path to store GGUF language models. Defaults to `ACP_BASE_DIR/llm_models`.
        *   `WORK_SESSIONS_DIR`: Path to store work session data. Defaults to `ACP_BASE_DIR/work_sessions`.
        *   Other settings like `LLM_BACKEND_TYPE`, `LLAMA_CPP_*` parameters can be configured as needed.
5.  **Running the Backend Server:**
    *   Use the PDM script for development (includes auto-reload and debug logging):
        ```bash
        pdm run dev
        ```
    *   This typically starts the Uvicorn server on `http://localhost:8000`.
6.  **Linting & Formatting:**
    *   To check for linting issues:
        ```bash
        pdm run lint
        ```
    *   To automatically format code:
        ```bash
        pdm run format
        ```

---

### 6. Testing

The project uses `pytest` for testing, with `pytest-asyncio` for asynchronous code and `pytest-mock` for mocking.

1.  **Running Tests:**
    *   Execute all tests using the PDM script:
        ```bash
        pdm run test
        ```
2.  **Test Structure:**
    *   **Unit Tests:** Located in `tests/unit/`. These test individual modules and functions in isolation.
    *   **Integration Tests:** Located in `tests/integration/`. These test the interaction between different components of the backend, including API endpoints.
3.  **Key Fixtures:**
    *   `tests/integration/conftest.py` defines crucial fixtures for integration testing. This includes fixtures that override the FastAPI dependencies for core services (`SessionHandler`, `LLMManager`, `AgentConfigHandler`, etc.) with test-specific instances or mocks. This is vital for creating a controlled test environment.
    *   The `patch_anyio_event_for_sse` fixture is specifically important for testing SSE streaming endpoints to ensure compatibility with Pytest's asyncio event loop.

---

### 7. Path to a Fully Functional AI Workspace Web Interface (Next Steps & Future Development)

The primary focus moving forward is the development of a web-based user interface and the full implementation of core backend functionalities that are currently placeholders.

**A. Frontend Development (High Priority):**

*   **Technology Selection:**
    *   Evaluate and select a modern web framework. Options include React, Vue.js, Svelte, Lit, or potentially a simpler server-interfacing library like HTMX if a less SPA-heavy approach is desired for initial versions.
*   **API Client Implementation:**
    *   Develop a robust client-side service or set of utilities to communicate with the FastAPI backend. This should handle request/response cycles, error management, and importantly, SSE stream consumption.
*   **Core UI Components Development:**
    *   **LLM Management Dashboard:** Interface to list available/loaded models, display their status, and trigger load/unload operations.
    *   **Agent Configuration UI:** Forms and views for creating, viewing, and editing both global and session-scoped agent configurations.
    *   **Agent Execution UI:** Allow users to select an agent, provide input prompts/parameters, initiate agent runs (both blocking and streaming), and view progress/outputs.
    *   **Work Session Management UI:** Interface for creating new sessions, listing existing ones, selecting an active session to work in, and deleting sessions.
    *   **"Canvas" Area / File Explorer:** A visual browser for the files and directories within the active work session's `data/` directory (interacting with the WorkBoard API). Basic file viewing and editing capabilities would be a starting point.
    *   **Chat Interface:** A dedicated UI for direct chat interactions with loaded LLMs. This could later be extended for chat-based agent interactions.
    *   **Real-time Log/Output Display:** A component to render streaming data from SSE endpoints (agent outputs, LLM tokens) in a user-friendly way.

**B. Backend Enhancements & Feature Completion:**

*   **User Authentication & Authorization (Basic):**
    *   Implement a simple authentication mechanism suitable for a locally hosted, trusted environment. Options:
        *   Static API key passed via HTTP header (configurable in `.env`).
        *   Basic HTTP Authentication (username/password).
    *   Avoid over-engineering for the initial local DIY use case; more complex auth can be added if the project evolves towards multi-user or public-facing scenarios.
*   **`smolagents` Full Integration:**
    *   Transition the `AgentExecutor` from placeholder logic to a full implementation utilizing the `smolagents` library. This includes:
        *   Defining how agents receive initial prompts, context (e.g., session history, relevant files from the work board), and configuration.
        *   Implementing concrete agent "tools" or capabilities. Examples:
            *   File system operations via `FileSystemManager`.
            *   Web search (e.g., using the `SERPER_API_KEY` if configured).
            *   A sandboxed code execution environment for agents that need to run scripts.
        *   Establishing the agent lifecycle (start, run, stop, error states) and how agent state is managed or persisted (if required beyond session files).
        *   Ensuring agent output (especially streaming chunks) is well-structured and contains necessary metadata for clear UI presentation.
*   **Advanced Canvas/WorkBoard Features (Future Consideration):**
    *   Depending on the "canvas" UI vision, the WorkBoard API might need extensions for richer file metadata, simple file versioning, or specialized handling/previewing of common AI-related file types (e.g., notebooks, datasets).
*   **WebSockets (Optional Evaluation):**
    *   While SSE is suitable for unidirectional server-to-client streams, evaluate if any planned UI features would significantly benefit from bidirectional, low-latency communication offered by WebSockets (e.g., real-time collaborative editing on the "canvas", interactive agent control beyond simple prompting).
*   **(Optional) `PIEBackend` Implementation:**
    *   If supporting alternative LLM backends beyond `llama-cpp-python` (e.g., connecting to a `text-generation-inference` server via a "PIE" - Python Inference Endpoint - client) becomes a priority, complete this implementation.

**C. API Iteration:**

*   As frontend development progresses and user interaction patterns become clearer, anticipate the need to refine existing API endpoints or add new ones to better support the UI. Maintain clear API contracts and versioning if necessary.

**D. Enhanced Documentation & OSS Readiness:**

*   **API Documentation:** Continuously leverage FastAPI's auto-generated OpenAPI docs (`/docs` and `/redoc`). Supplement this with narrative documentation (e.g., using MkDocs or similar) explaining concepts, workflows, and advanced usage.
*   **Developer Guide:** Create and maintain a guide for developers covering project setup, architecture deep-dive, how to add new features (e.g., new agent tools, new API endpoints), and coding conventions.
*   **Community Files:**
    *   `CONTRIBUTING.md`: Guidelines for contributing to the project (code style, pull request process, issue reporting).
    *   `CODE_OF_CONDUCT.md`: Establish community standards.
*   **Test Coverage:** Maintain and expand test coverage, especially for new backend features and API endpoints critical for the web interface.

**E. Packaging & Distribution (Initial Local Focus):**

*   **Installation Script:** Review and improve the existing `install_acp.sh` for robustness and user-friendliness across different Linux distributions.
*   **Dockerization (Consideration):** Develop a simple Dockerfile and `docker-compose.yml` setup. This can significantly ease local deployment for users by encapsulating dependencies and providing a consistent runtime environment, especially important for DIY hardware setups.

---

### 8. Deployment & Operational Considerations (Local DIY Focus)

*   **Target Environment:** Primarily Linux-based DIY machines (e.g., Ubuntu is a common user choice). The backend should be runnable on any system meeting Python and core dependency requirements.
*   **Access Model:** The primary access method is via a web browser on the local network, connecting to the FastAPI server hosted on the DIY machine.
*   **Resource Management:** Users must be made aware that running LLMs, especially larger ones, requires significant RAM and, for GPU-accelerated models (`llama-cpp-python` with GPU layers), VRAM. The backend application itself is relatively lightweight.
*   **Python Environment:** PDM creates and manages a project-local virtual environment (typically in `.venv/` within the project root), ensuring dependency isolation.
*   **Data Persistence:** All critical data is stored on the local file system:
    *   Work session data (including user files, local agent configurations, and session manifests) is stored under the configured `WORK_SESSIONS_DIR/<session_id>/`.
    *   Global agent configurations are stored as JSON files in `WORK_SESSIONS_DIR/_agent_configs/`.
    *   LLMs are expected to be managed by the user within the `MODELS_DIR`.
    *   Application logs are written to `LOG_DIR`.
    *   (Note: All these base paths are configurable via the `.env` file and default to subdirectories under `ACP_BASE_DIR`).
*   **Backup Strategy:** Users should be advised to regularly back up their `ACP_BASE_DIR` (or the custom paths they configure for `MODELS_DIR`, `WORK_SESSIONS_DIR`, etc.) to prevent data loss.

---

### 9. Philosophy & Guiding Principles

*   **Solid Backend First:** The project prioritizes a robust, well-tested, and modular backend as the stable foundation upon which further functionalities and the UI are built.
*   **Local Control & Open Models:** A core tenet is to empower users with control over their AI tools and data by enabling the use of open-source and locally run LLMs (with a current focus on GGUF formats).
*   **Open Source & Community Collaboration:** The project is intended to be open-source (MIT License) to foster a collaborative community, encouraging contributions, adaptations, and shared learning.
*   **Self-Sufficient Workspace (Dogfooding):** The aspirational goal is for AiCockpit to evolve into a powerful AI workspace that can be used for its own development, embodying the principles of "eating your own dog food."
