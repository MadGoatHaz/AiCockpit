# acp_backend/main.py
import logging
import logging.config
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse # Ensure EventSourceResponse is imported for routers that stream

from acp_backend.config import settings 
from acp_backend.models.common import StatusResponse

# Import router modules
from acp_backend.routers import system as system_router
from acp_backend.routers import llm_service as llm_service_router
from acp_backend.routers import agents as agents_router
from acp_backend.routers import work_sessions as work_sessions_router
from acp_backend.routers import work_board as work_board_router

# Configure logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s - %(name)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        "acp_backend": {"handlers": ["default"], "level": "DEBUG" if settings.DEBUG_MODE else "INFO", "propagate": False},
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
    },
}
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("acp_backend.main")


@asynccontextmanager
async def lifespan(current_app: FastAPI):
    logger.info(f"Starting up {settings.APP_NAME} v{settings.APP_VERSION}...")
    logger.info(f"Debug mode: {'on' if settings.DEBUG_MODE else 'off'}")
    logger.info(f"WORK_SESSIONS_DIR: {settings.WORK_SESSIONS_DIR}")
    logger.info(f"GLOBAL_AGENT_CONFIGS_DIR: {settings.get_global_agent_configs_path()}")
    logger.info(f"MODELS_DIR: {settings.MODELS_DIR}")
    logger.info(f"LOG_DIR: {settings.LOG_DIR}")
    logger.info(f"TEMP_DIR: {settings.TEMP_DIR}")

    # Accessing handlers here will trigger their instantiation via dependencies.py
    # This ensures they are initialized when the app starts.
    from acp_backend.dependencies import get_session_handler_dependency, get_llm_manager_dependency, get_agent_config_handler_dependency, get_fs_manager_dependency, get_agent_executor_dependency
    
    # Trigger instantiation and log status
    try:
        session_h = get_session_handler_dependency()
        logger.info(f"SessionHandler initialized. Base dir: {session_h.sessions_base_dir}")
    except HTTPException as e: logger.critical(f"Failed to initialize SessionHandler: {e.detail}")

    try:
        llm_m = get_llm_manager_dependency()
        if llm_m: logger.info(f"LLMManager initialized. Backend: {settings.LLM_BACKEND_TYPE}")
        else: logger.warning("LLMManager not initialized (module disabled or error).")
    except HTTPException as e: logger.critical(f"Failed to initialize LLMManager: {e.detail}")

    try:
        agent_config_h = get_agent_config_handler_dependency()
        logger.info(f"AgentConfigHandler initialized. Global path: {agent_config_h.global_configs_base_path}")
    except HTTPException as e: logger.critical(f"Failed to initialize AgentConfigHandler: {e.detail}")

    try:
        fs_m = get_fs_manager_dependency()
        logger.info(f"FileSystemManager initialized. Uses session handler: {type(fs_m.session_handler)}")
    except HTTPException as e: logger.critical(f"Failed to initialize FileSystemManager: {e.detail}")

    try:
        agent_exec = get_agent_executor_dependency()
        logger.info(f"AgentExecutor initialized. Uses config handler: {type(agent_exec.agent_config_handler)}")
    except HTTPException as e: logger.critical(f"Failed to initialize AgentExecutor: {e.detail}")

    yield 

    logger.info(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for AiCockpit (ACP).",
    lifespan=lifespan 
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# Include routers
if settings.ENABLE_SYSTEM_MODULE:
    app.include_router(system_router.router, prefix="/api/system", tags=["System"])
    logger.info("System module enabled and router included.")
else:
    logger.info("System module is disabled.")
    @app.get("/api/system/{path:path}", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    async def system_disabled_placeholder(): return {"detail": "System Service is currently disabled."}

if settings.ENABLE_LLM_MODULE:
    app.include_router(llm_service_router.router, prefix="/api/llm", tags=["LLM Service"])
    logger.info("LLM Service module enabled and router included.")
else:
    logger.info("LLM Service module is disabled.")
    @app.get("/api/llm/{path:path}", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    async def llm_disabled_placeholder(): return {"detail": "LLM Service is currently disabled."}

if settings.ENABLE_AGENT_MODULE:
    app.include_router(agents_router.router, prefix="/api/agents", tags=["Agent Service"])
    logger.info("Agents module enabled and router included.")
else:
    logger.info("Agents module is disabled.")
    @app.get("/api/agents/{path:path}", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    async def agents_disabled_placeholder(): return {"detail": "Agent Service is currently disabled."}

if settings.ENABLE_WORK_SESSION_MODULE:
    app.include_router(work_sessions_router.router, prefix="/api/sessions", tags=["Work Sessions"])
    logger.info("Work Sessions module enabled and router included.")
else:
    logger.info("Work Sessions module is disabled.")
    @app.get("/api/sessions/{path:path}", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    async def sessions_disabled_placeholder(): return {"detail": "Work Session Service is currently disabled."}

if settings.ENABLE_WORK_BOARD_MODULE:
    app.include_router(work_board_router.router, prefix="/api/workboard", tags=["WorkBoard Service"]) 
    logger.info("WorkBoard module enabled and router included.")
else:
    logger.info("WorkBoard module is disabled.")
    @app.get("/api/workboard/{path:path}", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    async def workboard_disabled_placeholder(): return {"detail": "WorkBoard Service is currently disabled."}

@app.get("/", response_model=StatusResponse, tags=["Root"])
async def get_root_status():
    return StatusResponse(status="ok", message=f"Welcome to {settings.APP_NAME} v{settings.APP_VERSION}.")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting Uvicorn server for {settings.APP_NAME} on port {settings.APP_PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=settings.APP_PORT)
