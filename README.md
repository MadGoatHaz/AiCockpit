<div align="center">
  <!-- ![AiCockpit Logo](placeholder_for_logo.png) -->
  <h1>🚀 AiCockpit 🚀</h1>
  <p><strong>Your Self-Hosted, AI-Powered Command Center for Local Development & Creativity!</strong></p>
  <p>
    <!-- Placeholder for badges -->
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT">
    <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
    <img src="https://img.shields.io/badge/Next.js-15.2.3-green.svg" alt="Next.js 15.2.3">
    <img src="https://img.shields.io/badge/React-18.3.1-blue.svg" alt="React 18.3.1">
    <img src="https://img.shields.io/badge/status-alpha-orange.svg" alt="Status: Alpha">
    <!-- Add more badges as needed: build status, coverage, etc. -->
  </p>
</div>

---

## 👋 Welcome to AiCockpit!

**AiCockpit (ACP)** is an ambitious open-source project to create a locally hosted backend API and, ultimately, a full-fledged web application. Imagine a powerful, private workspace, running on your own hardware, where you can seamlessly manage Large Language Models (LLMs), orchestrate AI agents, and organize your projects with AI assistance.

Our vision extends far beyond creating a simple alternative to cloud-based AI tools. We aim to build **THE definitive, self-hosted, DIY Ai workspace for everyone.** AiCockpit is designed to be easily installable, accessible on your local network (or via your own VPN for secure remote access), ensuring your data remains entirely within your control, on your hardware. 

While prioritizing local AI and data sovereignty, AiCockpit will also embrace a **hybrid approach**, enabling you to seamlessly integrate and manage cloud-based AI services alongside your local models. This allows for a powerful collaborative environment where different AI capabilities (local and remote) can contribute to various aspects of your projects.

The ultimate aspiration for AiCockpit is to evolve into a **comprehensive, collaborative Ai work environment that verges on being an operating system in itself.** We envision a future where you can interact with AiCockpit not just through typing, but through **voice commands** and other intuitive modalities, unlocking new levels of productivity and creative partnership with AI. It's about building a foundational platform for human-AI collaboration on *any* conceivable project.

**Current Version:** 0.2.5-alpha (Backend Stable, Frontend In Progress)
**Last Updated:** May 30, 2025

---

## 🌟 Core Vision

AiCockpit is not just another AI tool; it's envisioned as **the ultimate self-hosted, AI-powered command center for boundless creativity and productivity.** We aim to build a deeply integrated workspace where humans and AI collaborate seamlessly on *any* project imaginable.

**AiCockpit aspires to empower you to:**

*   🧠 **Master Your LLMs:** Effortlessly discover, download, manage, and interact with a diverse range of local Large Language Models (GGUF focus, with an eye towards future formats and integrations). Go beyond simple chat to fine-tune, experiment, and truly own your AI interactions.
*   🤖 **Orchestrate Intelligent Agents:** Define, configure, and deploy sophisticated AI agents (powered by frameworks like `smolagents` and beyond). Equip them with tools to automate complex workflows, conduct research, manage tasks, and act as specialized assistants for your projects.
*   💻 **Supercharge Code Development:** From initial scaffolding and boilerplate generation to advanced debugging, code explanation, refactoring, and automated testing, AiCockpit will be an indispensable co-pilot for software engineers.
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
    *   Each session has its own isolated data storage.
*   📋 **Work Board (File System Access):**
    *   Manage files and directories within each session (list, read, write, delete, move, create directory).
*   ⚙️ **System & Configuration:**
    *   Endpoints for system health, status, and viewing configurations.
*   🛡️ **Stability & Testing:**
    *   Comprehensive test suite with 100% pass rate (as of the last major refactor).
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
*   ⚙️ **UI Components (ShadCN based):** Core elements like `Button`, `Card`, `Tooltip`, `Sheet`, `DropdownMenu`, `Tabs` (base), and `Chart` (base) are integrated.
*   💡 **Persistent Info Widgets:** Toggleable overlay widgets for CPU, Memory, etc., displaying mock data.
*   🤖 **Genkit Integration (Initial):** Basic structure for Genkit flows (e.g., `summarize-logs`).
*   🧩 **Workspaces Page (`/interact`):**
    *   **Tabbed Interface:** Implemented using ShadCN `Tabs` for managing multiple workspaces.
    *   **Resizable Panel Layout:** A three-panel horizontal layout (File Browser, Editor/Terminal, AI Chat/Settings) within each workspace tab, built with `react-resizable-panels`. The central panel is further split vertically.
    *   **Core Panel Implementation (Mock UIs):**
        *   `FileBrowserPanel.tsx`: Displays a mock file tree with folder expansion/collapse and file selection interactivity.
        *   `EditorPanel.tsx`: Shows a mock text area, dynamically updates with the selected file name from the File Browser.
        *   `TerminalManagerPanel.tsx`: Provides a mock terminal interface with command input, output display, and basic command history.
        *   `AiChatPanel.tsx`: Features a mock chat interface with user/AI message display and input.
        *   `WorkspaceSettingsPanel.tsx`: Basic UI for displaying workspace ID and placeholder settings.

---

## 🛣️ Roadmap & Current Focus

**High Priority: Enhancing the Frontend Web Interface, particularly the "Workspaces" page.**

**Key Milestones & Next Steps:**

1.  🌟 **Frontend Development (Phase 1 - Core UI): In Progress**
    *   **Technology Selection: Done!** (Next.js, React, TypeScript, ShadCN UI, Tailwind CSS)
    *   **Core Layout & Navigation: Done!** (AppSidebar, HeaderBar, Toaster, basic page structure)
    *   **Dashboard (AiSight) Implementation: Done!** (KeyMetricsCards, SystemHealthChart, ModelPerformanceChart with mock data)
    *   **Persistent Info Widgets: Done!** (Toggleable display of mock system stats)
    *   **Base UI Components (ShadCN): Done!** (Button, Card, Tooltip, Sheet, DropdownMenu, Tabs, Chart)
    *   **Workspaces Page (`/interact`): Current Focus - Partially Done**
        *   Implement tabbed interface for managing multiple workspaces: **Done!**
        *   Develop core panels within a workspace: File Browser, AI Chat, File Viewer, Workspace Settings, AI Model & Parameters, Terminal Manager: **Initial mock UIs and basic interactivity for all five core panels implemented (FileBrowser, Editor, TerminalManager, AiChat, WorkspaceSettings).**
        *   Simulate client-side file operations and AI interactions as placeholders for backend integration: **Basic file selection linked to editor display is functional.**
        *   **MHTML Mockup Review & Future Considerations:** An `AiCockpit.mhtml` mockup provided by the user was reviewed. It showcases an alternative, more complex grid-based panel layout within workspaces, with individual panel controls (visibility, S/M/L sizing, height). It also details richer features for each panel (e.g., upload in File Browser, model selection & advanced settings in AI Chat, internal tabs in Terminal, extensive workspace/model tuning settings). These provide valuable insights for future enhancements and potential layout refactoring.
    *   API client for seamless backend communication (including SSE).
2.  🤖 **Backend Enhancements (Parallel/Future):**
    *   **Full `smolagents` Integration:** Implement the agent execution logic beyond the current placeholder.
    *   **Basic User Authentication:** Simple, secure auth for a local-first setup.
3.  🌱 **OSS Readiness & Community Building (Ongoing):**
    *   Enhance API documentation (OpenAPI + narrative docs).
    *   Create a comprehensive Developer Guide.
    *   Maintain `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`.

*(For a more granular breakdown of the backend's history, see the original `AiCockpit outline - Handoff Doc.txt`.)*

---

## 🛠️ Tech Stack Snapshot

*   **Backend:** Python 3.10+, FastAPI, Uvicorn
*   **LLM Integration:** `llama-cpp-python` (for GGUF models)
*   **Agent Framework:** `smolagents` (initial integration)
*   **Async & Streaming:** `asyncio`, `anyio`, `sse-starlette`
*   **Data Validation:** Pydantic v2, Pydantic-Settings
*   **DevOps:** PDM (dependency management), `pytest` (testing), Ruff (linting), Black (formatting)
*   **Frontend:**
    *   Framework: Next.js (v15.2.3, App Router)
    *   UI Library: React (v18.3.1), ShadCN UI
    *   Language: TypeScript
    *   Styling: Tailwind CSS, CSS Variables (custom theme)
    *   AI Toolkit Integration: Genkit (v1.8.0, initial setup)
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
    pdm run dev
    ```
    *   Server usually starts on `http://localhost:8000`.
    *   API docs at `http://localhost:8000/docs`.

### 2. Frontend Setup

*   **Prerequisites:**
    *   Node.js (v18.x or later recommended) and npm/yarn.
*   **Navigate to Frontend Directory:**
    ```bash
    cd acp_frontend
    ```
*   **Install Dependencies:**
    ```bash
    npm install
    # OR
    # yarn install
    ```
    *   This will install Next.js, React, ShadCN UI dependencies (including Radix UI primitives), `recharts`, `lucide-react`, Genkit tools, etc., as defined in `package.json`.
*   **Run the Frontend Development Server:**
    ```bash
    npm run dev
    # OR
    # yarn dev
    ```
    *   The frontend application usually starts on `http://localhost:3000`.

### 3. Linting & Formatting

*   **Backend:**
    ```bash
    pdm run lint
    pdm run format
    ```
*   **Frontend:** (Assuming standard Next.js/ESLint setup)
    ```bash
    npm run lint
    npm run format # If a format script is configured in package.json
    ```

### 4. Running Tests

*   **Backend:**
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
    *   **Frontend (TypeScript/React):** Adhere to Prettier/ESLint configurations (typically in `package.json` and `.eslintrc.js`).
*   **Component Design (Frontend):**
    *   Favor functional components with React Hooks.
    *   Strive for modular, reusable components. Place general UI primitives in `src/components/ui/` and feature-specific components in `src/components/[feature]/`.
    *   Utilize ShadCN UI components as a base and customize as needed.
    *   Clearly define props using TypeScript interfaces.
*   **State Management (Frontend):**
    *   Lift state to the lowest common ancestor. For more complex global state, consider Zustand or React Context if useState/props become unwieldy.
    *   "use client" directive for components requiring client-side interactivity or browser APIs. Default to Server Components where possible for performance.
*   **Styling (Frontend):**
    *   Utility-first with Tailwind CSS.
    *   Use the `cn` utility from `@/lib/utils` for conditional class names.
    *   Leverage HSL CSS variables in `globals.css` for theming.
*   **API Interaction:**
    *   Backend APIs are defined with FastAPI and documented via OpenAPI (`/docs`).
    *   Frontend should create typed service functions for API calls, potentially in `src/lib/api.ts` or similar.
*   **Testing:**
    *   **Backend:** Write unit tests for new logic and integration tests for API endpoints. Aim for high test coverage.
    *   **Frontend:** (Future) Implement unit/integration tests for components and critical user flows using Jest/React Testing Library or Vitest.
*   **Documentation:**
    *   Document non-trivial code with JSDoc/TSDoc or Python docstrings.
    *   Keep `README.md` and other architectural documents up-to-date with major changes.
    *   For UI components, consider using Storybook in the future for isolated development and documentation.
*   **AI Collaboration:**
    *   When pair-programming with an AI, provide clear context (relevant files, detailed instructions).
    *   Review AI-generated code cambios thoroughly.
    *   Iterate with the AI; don't expect perfect solutions on the first try.
    *   Use the AI to help with boilerplate, refactoring, writing tests, and explaining code.

### AI Collaboration & Handoff Document

*   **General AI Collaboration:**
    *   When pair-programming with an AI, provide clear context (relevant files, detailed instructions).
    *   Review AI-generated code changes thoroughly.
    *   Iterate with the AI; don't expect perfect solutions on the first try.
    *   Use the AI to help with boilerplate, refactoring, writing tests, and explaining code.
*   **`ACP Handoffdoc.txt` (For AI Assistants):**
    *   This document (located at the project root) serves as a persistent memory and handoff mechanism between AI-assisted development sessions.
    *   Its purpose is for the AI assistant to log a summary of work completed, current project status, key decisions, and next steps at the end of a work session.
    *   This allows any AI assistant (the same one in a new session, or a different one) to quickly get up to speed on the project's state.
    *   The AI assistant is encouraged to manage this file, including summarizing or pruning very old information to keep it relevant and manageable.
    *   *Note: This file is primarily for AI-to-AI communication, not as primary human-readable project documentation, though it can serve as a detailed historical log.*

---

## 🛠 How to Contribute

We're thrilled you're considering contributing! Here's how you can help:

1.  **Check out the Roadmap:** See what's currently in focus.
2.  **Browse Open Issues:** Look for `good first issue` or `help wanted` tags (we'll add these soon!).
3.  **Discuss Your Ideas:** Open an issue or join our (future) communication channel to discuss potential changes or new features.
4.  **Fork & Pull Request:**
    *   Fork the repository.
    *   Create a new branch for your feature or bugfix.
    *   Make your changes, adhering to code style (run formatters).
    *   Ensure tests pass. Add new tests for new functionality.
    *   Submit a pull request with a clear description of your changes.

Detailed contribution guidelines will be in `CONTRIBUTING.md`.

---

## 📜 License

AiCockpit is licensed under the [MIT License](LICENSE).

---

*(The more detailed project history, initial planning, and in-depth component descriptions are preserved in `AiCockpit outline - Handoff Doc.txt` for reference.)*
