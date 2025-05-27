import logging
from fastapi import APIRouter, HTTPException, status
from acp_backend.config import settings, Settings 
from acp_backend.models.common import StatusResponse, PingResponse

logger = logging.getLogger(__name__)
router = APIRouter()
MODULE_NAME = "System Service"
TAG_SYSTEM_INFO = "System Information"

def _check_module_enabled():
    if not settings.ENABLE_SYSTEM_MODULE:
        logger.warning(f"{MODULE_NAME} is disabled in configuration.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{MODULE_NAME} is currently disabled."
        )

@router.get(
    "/status", 
    response_model=StatusResponse, 
    summary="Get System Status and Basic Info",
    tags=[TAG_SYSTEM_INFO]
)
async def get_system_status():
    _check_module_enabled()
    logger.debug("Request for system status.")
    
    enabled_modules_status = {
        "llm_service": {"enabled": settings.ENABLE_LLM_MODULE, "status": "ok" if settings.ENABLE_LLM_MODULE else "disabled"},
        "agents_service": {"enabled": settings.ENABLE_AGENT_MODULE, "status": "ok" if settings.ENABLE_AGENT_MODULE else "disabled"},
        "work_sessions_service": {"enabled": settings.ENABLE_WORK_SESSION_MODULE, "status": "ok" if settings.ENABLE_WORK_SESSION_MODULE else "disabled"},
        "work_board_service": {"enabled": settings.ENABLE_WORK_BOARD_MODULE, "status": "ok" if settings.ENABLE_WORK_BOARD_MODULE else "disabled"}
    }
    
    application_status = "ok" 

    return StatusResponse(
        status=application_status, 
        message=f"{settings.APP_NAME} v{settings.APP_VERSION} is running.",
        details={
            "application_name": settings.APP_NAME,
            "application_version": settings.APP_VERSION,
            "debug_mode": settings.DEBUG_MODE,
            "configured_llm_backend": settings.LLM_BACKEND_TYPE if settings.ENABLE_LLM_MODULE else "N/A (LLM Module Disabled)",
            "modules": enabled_modules_status
        }
    )

@router.get(
    "/ping", 
    response_model=PingResponse, 
    summary="Ping System for Liveness Check",
    tags=[TAG_SYSTEM_INFO]
)
async def ping_system():
    _check_module_enabled()
    logger.debug("Ping request received, sending pong.")
    return PingResponse()

@router.get(
    "/config/view", 
    response_model=Settings, 
    summary="View System Configuration (Review for Production)",
    tags=[TAG_SYSTEM_INFO]
)
async def get_system_config_view():
    """
    Displays the current system configuration settings loaded from environment
    variables and defaults. 
    
    **Caution**: This endpoint returns the full `Settings` object. 
    In a production environment, ensure that sensitive values (e.g., API keys like 
    `SERPER_API_KEY`) are not inadvertently exposed. Consider using a separate response 
    model that excludes sensitive fields or implementing proper authorization.
    """
    _check_module_enabled()
    # (Future - Category 3) Add authorization check here if this endpoint is sensitive
    # if not current_user.is_admin: 
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")

    logger.info("Request to view system configuration.")
    return settings
