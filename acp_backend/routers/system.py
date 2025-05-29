# acp_backend/routers/system.py
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from acp_backend.config import AppSettings
from acp_backend.dependencies import get_app_settings
from acp_backend.models.common import PingResponse, StatusResponse

logger = logging.getLogger(__name__)
router = APIRouter()
MODULE_NAME = "System Service"
TAG_SYSTEM_INFO = "System Information"

# Type Alias for Dependency
SettingsDep = Annotated[AppSettings, Depends(get_app_settings)]


def _check_module_enabled(current_settings: SettingsDep):
    if not current_settings.ENABLE_SYSTEM_MODULE:
        logger.warning(f"{MODULE_NAME} is disabled in configuration.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{MODULE_NAME} is currently disabled.",
        )


@router.get(
    "/status",
    response_model=StatusResponse,
    summary="Get System Status and Basic Info",
    tags=[TAG_SYSTEM_INFO],
    dependencies=[Depends(_check_module_enabled)],
)
async def get_system_status(current_settings: SettingsDep):
    logger.debug("Request for system status.")

    enabled_modules_status = {
        "llm_service": {
            "enabled": current_settings.ENABLE_LLM_SERVICE_MODULE,
            "status": "ok"
            if current_settings.ENABLE_LLM_SERVICE_MODULE
            else "disabled",
        },
        "agents_service": {
            "enabled": current_settings.ENABLE_AGENTS_MODULE,
            "status": "ok" if current_settings.ENABLE_AGENTS_MODULE else "disabled",
        },
        "work_sessions_service": {
            "enabled": current_settings.ENABLE_WORK_SESSIONS_MODULE,
            "status": "ok"
            if current_settings.ENABLE_WORK_SESSIONS_MODULE
            else "disabled",
        },
        "work_board_service": {
            "enabled": current_settings.ENABLE_WORK_BOARD_MODULE,
            "status": "ok"
            if current_settings.ENABLE_WORK_BOARD_MODULE
            else "disabled",
        },
    }

    application_status = "ok"
    app_name = getattr(current_settings, "APP_NAME", "AiCockpit Backend")
    debug_mode = getattr(current_settings, "DEBUG_MODE", current_settings.DEBUG)

    return StatusResponse(
        status=application_status,
        message=f"{app_name} v{current_settings.APP_VERSION} is running.",
        details={
            "application_name": app_name,
            "application_version": current_settings.APP_VERSION,
            "debug_mode": debug_mode,
            "configured_llm_backend": current_settings.LLM_BACKEND_TYPE
            if current_settings.ENABLE_LLM_SERVICE_MODULE
            else "N/A (LLM Module Disabled)",
            "modules": enabled_modules_status,
        },
    )


@router.get(
    "/ping",
    response_model=PingResponse,
    summary="Ping System for Liveness Check",
    tags=[TAG_SYSTEM_INFO],
    dependencies=[Depends(_check_module_enabled)],
)
async def ping_system():
    logger.debug("Ping request received, sending pong.")
    return PingResponse()


@router.get(
    "/config/view",
    response_model=AppSettings,
    summary="View System Configuration (Review for Production)",
    tags=[TAG_SYSTEM_INFO],
    dependencies=[Depends(_check_module_enabled)],
)
async def get_system_config_view(current_settings: SettingsDep):
    logger.info("Request to view system configuration.")
    return current_settings
