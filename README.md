<div align="center">
  <!-- ![AiCockpit Logo](placeholder_for_logo.png) -->
  <h1>🚀 AiCockpit 🚀</h1>
  <p><strong>Your Self-Hosted, AI-Powered Command Center for Local Development & Creativity!</strong></p>
  <p>
    <!-- Placeholder for badges -->
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT">
    <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
    <img src="https://img.shields.io/badge/Next.js-15.3.2-green.svg" alt="Next.js 15.3.2">
    <img src="https://img.shields.io/badge/React-19.0.0-blue.svg" alt="React 19.0.0">
    <img src="https://img.shields.io/badge/status-alpha-orange.svg" alt="Status: Alpha">
    <!-- Add more badges as needed: build status, coverage, etc. -->
  </p>
</div>

---

## 📖 Table of Contents

*   [👋 Welcome to AiCockpit!](#-welcome-to-aicockpit)
*   [🌟 Core Vision](#-core-vision)
*   [✨ Key Features](#-key-features)
    *   [Backend (Solid & Ready!)](#backend-solid--ready)
    *   [Frontend (In Progress & Rapidly Evolving!)](#frontend-in-progress--rapidly-evolving)
*   [🛣️ Roadmap & Current Focus](#️-roadmap--current-focus)
*   [🚀 Next Steps / To-Do (Focus: Functional Polish & Core Features)](#-next-steps--to-do-focus-functional-polish--core-features)
*   [🛠️ Tech Stack Snapshot](#️-tech-stack-snapshot)
*   [🧑‍💻 Getting Started (Developers)](#-getting-started-developers)
    *   [Backend Setup](#1-backend-setup)
    *   [Frontend Setup](#2-frontend-setup)
    *   [Linting & Formatting](#3-linting--formatting)
    *   [Running Tests](#4-running-tests)
*   [✨ Best Practices & Development Notes](#-best-practices--development-notes)
*   [🤝 Contributing](#-contributing)
*   [📜 License](#-license)

---

## 👋 Welcome to AiCockpit!

**AiCockpit (ACP)** is an ambitious open-source project to create a locally hosted backend API and, ultimately, a full-fledged web application. Imagine a powerful, private workspace, running on your own hardware, where you can seamlessly manage Large Language Models (LLMs), orchestrate AI agents, and organize your projects with AI assistance.

Our vision extends far beyond creating a simple alternative to cloud-based AI tools. We aim to build **THE definitive, self-hosted, DIY Ai workspace for everyone.** AiCockpit is designed to be easily installable, accessible on your local network (or via your own VPN for secure remote access), ensuring your data remains entirely within your control, on your hardware. 

While prioritizing local AI and data sovereignty, AiCockpit will also embrace a **hybrid approach**, enabling you to seamlessly integrate and manage cloud-based AI services alongside your local models. This allows for a powerful collaborative environment where different AI capabilities (local and remote) can contribute to various aspects of your projects.

The ultimate aspiration for AiCockpit is to evolve into a **comprehensive, collaborative Ai work environment that verges on being an operating system in itself.** We envision a future where you can interact with AiCockpit not just through typing, but through **voice commands** and other intuitive modalities, unlocking new levels of productivity and creative partnership with AI. It's about building a foundational platform for human-AI collaboration on *any* conceivable project.

**Current Version:** 0.2.5-alpha (Backend Stable, Frontend In Progress)
**Last Updated:** May 29, 2024 (Reflecting recent frontend development sprint)

---

## 🌟 Core Vision

AiCockpit is not just another AI tool; it's envisioned as **the ultimate self-hosted, AI-powered command center for boundless creativity and productivity.** We aim to build a deeply integrated workspace where humans and AI collaborate seamlessly on *any* project imaginable.

**AiCockpit aspires to empower you to:**

*   🧠 **Master Your LLMs:** Effortlessly discover, download, manage, and interact with a diverse range of local Large Language Models (GGUF focus, with an eye towards future formats and integrations). Go beyond simple chat to fine-tune, experiment, and truly own your AI interactions.
*   🤖 **Orchestrate Intelligent Agents:** Define, configure, and deploy sophisticated AI agents (powered by frameworks like `smolagents` and beyond). Equip them with tools to automate complex workflows, conduct research, manage tasks, and act as specialized assistants for your projects.
*   🧑‍✈️ **Supercharge Code Development:** From initial scaffolding and boilerplate generation to advanced debugging, code explanation, refactoring, and automated testing, AiCockpit will be an indispensable co-pilot for software engineers.
*   🎨 **Unleash Creative Media Generation:** Extend beyond text and code. Imagine AiCockpit facilitating image generation, audio synthesis, video assistance, and other multimedia creation tasks by integrating with relevant models and tools, all managed within your local cockpit.
*   ✍️ **Elevate Content Creation:** Whether you're drafting articles, writing scripts, brainstorming ideas, or translating languages, AiCockpit will provide a rich environment for AI-assisted writing and content development.
*   🔬 **Drive Research & Analysis:** Utilize AI for data analysis, information retrieval, summarization of complex documents, and accelerating your research endeavors across any domain.
*   🛠️ **Build *Your* Perfect AI Workspace:** The core principle is **extensibility and customization**. If AiCockpit doesn't have a tool or integration you need, it will be designed to let you build it or plug it in. We envision a rich ecosystem of user-created plugins and extensions.
*   🗂️ **Achieve Total Project Organization:** Manage distinct work sessions, each with its own dedicated file system ("Work Board"), context, and persistent AI memory. Keep your diverse projects, from a software library to a novel, perfectly organized and AI-supercharged.
*   🌐 **Own Your Data, Own Your AI:** By being self-hosted, you maintain full control over your data, your models, and your AI interactions, ensuring privacy and security.
*   🔥 **Foster Open Innovation:** Built with Python, FastAPI, and a modular architecture (and now Next.js/React for the frontend!), AiCockpit is designed for community contributions. The ultimate dream? AiCockpit becoming so advanced it actively assists in its own development and helps users build the future of AI collaboration!

**In short: If you can dream of a project you can do with an AI, AiCockpit aims to be the self-hosted platform that helps you build it, manage it, and take it to the next level.**

---

## ✨ Key Features

### Backend (Solid & Ready!)

The AiCockpit backend provides a robust set of APIs for:

*   🔮 **LLM Management:**
    *   Discover available GGUF models.
    *   Load/unload models (via `llama-cpp-python`).
    *   Stream chat completions using Server-Sent Events (SSE).
*   🧑‍✈️ **AI Agent Orchestration:**
    *   Define global and session-specific agent configurations.
    *   Execute agents (current `smolagents` integration is a functional placeholder, ripe for full implementation!).
    *   Stream agent outputs via SSE.
*   🗂️ **Work Session Management:**
    *   Create, list, update, and delete distinct work sessions.
    *   Each session has its own isolated data storage and AI configuration.
*   📋 **Workspace File Management (Work Board):**
    *   Manage files and directories within each session (upload, list, read content, update content, create file/folder, delete file/folder).
*   🖥️ **Interactive Terminal Service:**
    *   WebSocket endpoint for PTY-based interactive terminal sessions within a workspace's data directory.
*   ⚙️ **System & Configuration:**
    *   Endpoints for system health, status, and viewing configurations.
*   🛡️ **Stability & Testing:**
    *   Comprehensive test suite (though coverage may vary with new features).
    *   Robust dependency injection for modularity.

### Frontend (In Progress & Rapidly Evolving!)

The AiCockpit frontend is being built with **Next.js (App Router), React, TypeScript, and ShadCN UI** for a modern, responsive, and themeable experience.

*   🎨 **Core Application Interface:**
    *   **Main Layout:** Collapsible sidebar for navigation, dynamic header bar.
    *   **Responsive Design:** Adapts for desktop and mobile viewing, including sheet-based mobile navigation.
    *   **Theming:** Custom HSL-based theme via Tailwind CSS.
    *   **Notifications:** Integrated toaster for user feedback.
*   🧭 **Navigation & Layout:**
    *   `AppSidebar` with active link highlighting and tooltips when collapsed.
    *   `HeaderBar` with mobile menu, desktop sidebar toggle, and a dropdown for toggling persistent info widgets.
*   📊 **Dashboard (AiSight Page):**
    *   `KeyMetricsCard` components displaying mock data for Active Agents, CPU/Memory Usage, Alerts, etc.
    *   `SystemHealthChart` (bar chart) and `ModelPerformanceChart` (line chart) with mock data, built using `recharts` and ShadCN chart components.
*   📄 **Placeholder Pages:** All main navigation items (`Workspaces`, `Logs`, `Alerts`, `History`, `Fleet`) have placeholder pages set up within the app layout.
*   ⚙️ **UI Components (ShadCN based):** Core elements like `Button`, `Card`, `Tooltip`, `Sheet`, `DropdownMenu`, `Tabs`, `Chart`, `Dialog`, `Input`, `Label`, `Switch`, `AlertDialog` etc., are integrated.
*   💡 **Persistent Info Widgets:** Toggleable overlay widgets for CPU, Memory, etc., displaying mock data.
*   🧩 **Workspaces Page (`/interact`): Core Functionality Connected**
    *   **Tabbed Interface:** For managing multiple workspaces.
    *   **CSS Grid Panel Layout:** For `FileBrowserPanel`, `EditorPanel`, `AiChatPanel` (with sub-tabs for AI Config & WS Settings), and `TerminalManagerPanel`.
    *   **`FileBrowserPanel`:** Full CRUD operations for files & folders, connected to backend.
    *   **`EditorPanel`:** Fetches, displays, and saves file content to/from backend.
    *   **`AiChatPanel`:** Streams responses from backend LLM service; uses shared AI model configuration.
    *   **`WorkspaceSettingsPanel`:** Loads and saves workspace name/description to backend.
    *   **`AIModelConfigurationPanel`:** Loads and saves AI model (ID, temperature) settings to backend per workspace.
    *   **`TerminalManagerPanel`:** Connects to backend WebSocket PTY for interactive terminal sessions.
*   🚀 **Xterm.js integration with fit and attach addons: ✅ **Done!**
*   🔒 **API client for seamless backend communication (including SSE): 🚧 **Partially Done** (Implemented on a per-component basis)
*   🛠️ **Next.js backend proxy/rewrites for API calls: ✅ **Done!**

## 🛣️ Roadmap & Current Focus

**High Priority: Enhancing the Frontend Web Interface, particularly the "Workspaces" page and connecting it to the backend.**

**Key Milestones & Next Steps:**

1.  🌟 **Frontend Development (Phase 1 - Core UI & Initial Backend Connection)**
    *   **Technology Selection: ✅ Done!** (Next.js, React, TypeScript, ShadCN UI, Tailwind CSS)
    *   **Core Layout & Navigation: ✅ Done!** (AppSidebar, HeaderBar, Toaster, basic page structure)
    *   **Dashboard (AiSight) Implementation: ✅ Done!** (KeyMetricsCards, SystemHealthChart, ModelPerformanceChart with mock data)
    *   **Persistent Info Widgets: ✅ Done!** (Toggleable display of mock system stats)
    *   **Base UI Components (ShadCN): ✅ Done!** (Button, Card, Tooltip, Sheet, DropdownMenu, Tabs, Chart, Dialog, Input, Label, Switch, AlertDialog, etc.)
    *   **Workspaces Page (`/interact`): 🚧 Core Functionality Implemented & Connected**
        *   Tabbed interface for multiple workspaces: ✅ **Done!**
        *   Core styling and theming: ✅ **Done!**
        *   CSS Grid panel layout (FileBrowser, Editor, TerminalManager, AiChat, Settings): ✅ **Done!**
        *   `FileBrowserPanel`:
            *   File/Folder Listing (from backend): ✅ **Done!**
            *   File Upload (to backend): ✅ **Done!**
            *   Create File/Folder (frontend & backend): ✅ **Done!**
            *   Delete File/Folder (frontend & backend): ✅ **Done!**
        *   `EditorPanel`:
            *   Fetch & Display File Content (from backend): ✅ **Done!**
            *   Save File Content (to backend): ✅ **Done!**
        *   `AiChatPanel`:
            *   Connect to streaming chat backend: ✅ **Done!**
            *   Basic UI placeholders for model selection: ✅ **Done!**
        *   `WorkspaceSettingsPanel`:
            *   UI for name/description, auto-save toggle: ✅ **Done!**
            *   Save name/description to backend: ✅ **Done!**
        *   `AIModelConfigurationPanel`:
            *   UI for model selection, temperature: ✅ **Done!**
            *   Fetch/Save AI config to backend: ✅ **Done!**
            *   Share config with `AiChatPanel`: ✅ **Done!**
        *   `TerminalManagerPanel`:
            *   Connect to backend WebSocket PTY: ✅ **Done!** (Verification pending stable backend startup)
            *   Xterm.js integration with fit and attach addons: ✅ **Done!**
    *   API client for seamless backend communication (including SSE): 🚧 **Partially Done** (Implemented on a per-component basis)
    *   Next.js backend proxy/rewrites for API calls: ✅ **Done!**

2.  🤖 **Backend Enhancements (Foundation & Workspace Features)**
    *   Core FastAPI setup, modular routers, dependency injection: ✅ **Done!**
    *   LLM Service (`/llm` endpoints for models, chat completions): ✅ **Done!**
    *   Work Session Management (`/sessions` endpoints for CRUD, AI config): ✅ **Done!**
    *   Workspace Files Module (`/workspaces/sessions/.../files` endpoints):
        *   Upload, List, Get Content, Update Content, Create, Delete: ✅ **Done!**
    *   Terminal Service (`/terminals` WebSocket endpoint): ✅ **Done!** (Verification pending stable startup)
    *   **Full `smolagents` Integration:** ⏳ Implement the agent execution logic beyond the current placeholder.
    *   **Basic User Authentication:** ⏳ Simple, secure auth for a local-first setup.
    *   Maintain `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`.

*(For a more granular breakdown of the backend's history, see the original `AiCockpit outline - Handoff Doc.txt`.)*

## 🚀 Next Steps / To-Do (Focus: Functional Polish & Core Features)

This section outlines the immediate priorities to bring AiCockpit to a more robust and functionally complete state.

1.  **✅ Verify & Stabilize Core `Workspaces` (`/interact`) Functionality:**
    *   Thoroughly test all interactions between frontend panels (`FileBrowser`, `Editor`, `AiChat`, `TerminalManager`, `Settings`) and the live backend.
    *   Ensure WebSocket stability for the `TerminalManagerPanel`.
    *   Identify and resolve any persistent errors from backend connections or frontend rendering.

2.  **💅 Frontend Layout & Styling Issues: ✅ Adjusted for better balance.**
    *   Adjusted CSS grid proportions (`grid-rows-[3fr_1fr]`) on the `/interact` page for improved panel balance.
    *   Further user-resizable panel investigation deferred (previously attempted with `react-resizable-panels` causing issues).

3.  **🤖 Enhance `smolagents` Integration (Backend & Frontend):**
    *   Move beyond the current placeholder implementation.
    *   **Phase 1 Goal:** Allow users to select a predefined agent, provide a goal, and stream its output.
    *   Design and implement the necessary backend logic and frontend UI components for this.

4.  **🔒 Implement Basic User Authentication:**
    *   Add a simple and secure authentication mechanism (e.g., application-wide password) for local network access.
    *   Implement backend endpoints and frontend login UI.

5.  **🛠️ Refine Frontend API Client & State Management:**
    *   Centralize backend API interaction logic from individual components into a more robust API client module.
    *   Evaluate and potentially implement a more comprehensive global state management solution if needed.

6.  **📝 Continuous Documentation & Testing:**
    *   Keep `README.md` and `ACP Handoffdoc.txt` updated.
    *   Expand test coverage for new features and fixes.

---

## 🛠️ Tech Stack Snapshot

*   **Backend:** Python 3.10+, FastAPI, Uvicorn
*   **LLM Integration:** `llama-cpp-python` (for GGUF models)
*   **Agent Framework:** `smolagents` (initial integration)
*   **Async & Streaming:** `asyncio`, `anyio`, `sse-starlette`
*   **Data Validation:** Pydantic v2, Pydantic-Settings
*   **File Handling:** `python-multipart`
*   **Terminal:** `ptyprocess`
*   **DevOps:** PDM (dependency management), `pytest` (testing), Ruff (linting), Black (formatting)
*   **Frontend:**
    *   Framework: Next.js (v15.3.2, App Router)
    *   UI Library: React (v19.0.0), ShadCN UI
    *   Language: TypeScript
    *   Styling: Tailwind CSS, CSS Variables (custom theme)
    *   Terminal UI: Xterm.js (`@xterm/xterm`, `@xterm/addon-fit`, `@xterm/addon-attach`)
    *   Icons: lucide-react
    *   Charting: recharts (via ShadCN chart components)

---

## 🧑‍💻 Getting Started (Developers)

Ready to jump in? Here's how to get AiCockpit up and running:

### 1. Backend Setup

*   **Prerequisites:**
    *   Python 3.10+
    *   PDM: Install from [pdm-project.org](https://pdm-project.org/)
*   **Clone & Setup:**
    ```bash
    git clone https://github.com/your-username/aicockpit.git # Replace with your repo URL
    cd aicockpit
    pdm install -G dev
    ```
*   **Configure:**
    ```bash
    cp example.env .env
    ```
    *   Edit `.env` (especially `ACP_BASE_DIR`, `MODELS_DIR`).
*   **Run the Backend:**
    ```bash
    # From the project root directory (e.g., /home/g/Ai/AiCockpit)
    pdm run uvicorn acp_backend.main:app --reload --port 8000
    ```
    *   Server usually starts on `http://127.0.0.1:8000`.
    *   API docs at `http://localhost:8000/docs`.

### 2. Frontend Setup

*   **Prerequisites:**
    *   Node.js (v18.x or later recommended) and npm.
*   **Navigate to Frontend Directory:**
    ```bash
    # From the project root directory (e.g., /home/g/Ai/AiCockpit)
    cd acp_frontend
    ```
*   **Install Dependencies:**
    ```bash
    npm install
    ```
    *   This will install Next.js, React, ShadCN UI dependencies, Xterm.js, etc., as defined in `package.json`.
*   **Run the Frontend Development Server:**
    ```bash
    # From the acp_frontend directory
    npm run dev
    ```
    *   The frontend application usually starts on `http://localhost:3000` (or an available port if 3000 is in use).

### 3. Linting & Formatting

*   **Backend (from project root):**
    ```bash
    pdm run lint
    pdm run format
    ```
*   **Frontend (from `acp_frontend` directory):**
    ```bash
    npm run lint
    # Add a format script to package.json if desired, e.g., using Prettier
    # "format": "prettier --write ." 
    ```

### 4. Running Tests

*   **Backend (from project root):**
    ```bash
    pdm run test
    ```

---

## ✨ Best Practices & Development Notes

*(This section will be updated with guidelines and conventions as the project evolves. Contributions and suggestions are welcome!)*

*   **Commit Messages:** Follow conventional commit guidelines (e.g., `feat: add new login component`, `fix: resolve issue with API endpoint`). This helps in automated changelog generation and project tracking.
*   **Branching Strategy:** Use feature branches (e.g., `feature/HG-123-new-dashboard-widget` or `fix/HG-456-login-bug`). Create Pull Requests for review before merging to `main` or `develop` branch.
*   **Code Style:**
    *   **Backend (Python):** Adhere to Black for formatting and Ruff for linting (configured in `pyproject.toml`).
    *   **Frontend (TypeScript/React):** Adhere to Prettier/ESLint configurations (typically in `package.json` and relevant config files).
*   **Component Design (Frontend):**
    *   Favor functional components with React Hooks.
    *   Ensure components are modular and reusable where appropriate.
*   **Error Handling:** Implement comprehensive error handling on both frontend and backend to provide clear feedback to users and developers.
*   **Security:** Be mindful of security best practices, especially for file operations, API endpoints, and any user authentication mechanisms.

---

## 🤝 Contributing

Contributions are welcome! Please refer to `CONTRIBUTING.md` for detailed guidelines on how to contribute to AiCockpit.
The `CODE_OF_CONDUCT.md` outlines the expectations for community interactions.

---

## 📜 License

AiCockpit is licensed under the MIT License. See the `LICENSE` file for more details.
