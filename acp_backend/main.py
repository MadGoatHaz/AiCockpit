# acp_backend/main.py
import logging
from contextlib import asynccontextmanager
from typing import Annotated # Required for Annotated

from fastapi import FastAPI, Depends # Added Depends
from fastapi.middleware.cors import CORSMiddleware

# Import app_settings directly for use in lifespan, and AppSettings for type hint
from acp_backend.config import app_settings, AppSettings, setup_logging
from acp_backend.dependencies import (
    # These are the dependency provider functions
    get_agent_config_handler,
    get_agent_executor,
    get_fs_manager,
    get_llm_manager,
    get_session_handler,
    get_app_settings # Import the dependency getter for app_settings
)
from acp_backend.routers import agents, llm_service, system, work_board, work_sessions, workspace_files, terminal_service, workspaces

# Setup logging as early as possible
# Pass LOG_LEVEL from the already imported app_settings instance
setup_logging(log_level_str=app_settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # app_settings is already available globally from acp_backend.config
    
    logger.info(f"Starting up AiCockpit Backend v{app_settings.APP_VERSION}...")
    logger.info(f"Debug mode: {'on' if app_settings.DEBUG else 'off'}")

    logger.info(f"WORK_SESSIONS_DIR: {app_settings.WORK_SESSIONS_DIR}")
    logger.info(f"GLOBAL_AGENT_CONFIGS_DIR: {app_settings.GLOBAL_AGENT_CONFIGS_DIR}")
    logger.info(f"MODELS_DIR: {app_settings.MODELS_DIR}")
    logger.info(f"LOG_DIR: {app_settings.LOG_DIR}")
    logger.info(f"TEMP_DIR: {app_settings.TEMP_DIR}")

    logger.info("Lifespan startup: Core service singletons will be initialized on first use by an endpoint.")

    yield # Application runs here

    logger.info("Shutting down AiCockpit Backend...")
    pass


# Create FastAPI app instance
app = FastAPI(
    title="AiCockpit Backend (ACP)",
    description="Backend API for the AiCockpit AI-driven workspace.",
    version=app_settings.APP_VERSION,
    lifespan=lifespan,
)

# --- CORS Middleware Configuration ---
# TEMPORARILY ALLOW ALL ORIGINS FOR DEBUGGING
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ALLOW ALL ORIGINS - DEBUGGING ONLY
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- End CORS Middleware Configuration ---


# Include routers based on configuration
if app_settings.ENABLE_SYSTEM_MODULE:
    app.include_router(system.router, prefix="/system", tags=["System"])
    logger.info("System module enabled and router included.")

if app_settings.ENABLE_LLM_SERVICE_MODULE:
    app.include_router(llm_service.router, prefix="/llm", tags=["LLM Service"])
    logger.info("LLM Service module enabled and router included.")

if app_settings.ENABLE_AGENTS_MODULE:
    app.include_router(agents.router, prefix="/agents", tags=["Agents"])
    logger.info("Agents module enabled and router included.")

if app_settings.ENABLE_WORK_SESSIONS_MODULE:
    app.include_router(work_sessions.router, prefix="/sessions", tags=["Work Sessions"])
    logger.info("Work Sessions module enabled and router included.")

if app_settings.ENABLE_WORK_BOARD_MODULE:
    app.include_router(work_board.router, prefix="/sessions/{session_id}/work_board", tags=["Work Board"])
    logger.info("WorkBoard module enabled and router included.")

# Assuming a new config flag for this module
if app_settings.ENABLE_WORKSPACE_FILES_MODULE: 
    app.include_router(workspace_files.router, prefix="/workspaces", tags=["Workspace Files"]) # Using /workspaces prefix for consistency
    logger.info("Workspace Files module enabled and router included.")

if app_settings.ENABLE_TERMINAL_SERVICE_MODULE:
    app.include_router(terminal_service.router, prefix="/terminals", tags=["Terminal"])
    logger.info("Terminal Service module enabled and router included.")

# Add workspaces router
app.include_router(workspaces.router)
logger.info("Workspaces module enabled and router included.")


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to AiCockpit Backend v{app_settings.APP_VERSION}"}
