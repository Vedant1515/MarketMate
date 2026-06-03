import logging
from typing import Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings
from app.runtime_config import get_demo_mode, set_demo_mode


logger = logging.getLogger(__name__)

router = APIRouter()


class DemoModeRequest(BaseModel):
    enabled: bool


@router.get("/api/settings")
async def get_runtime_settings() -> Dict[str, Any]:
    settings = get_settings()
    return {
        "demo_mode": get_demo_mode(),
        "model": settings.llm_model,
        "llm_provider": settings.llm_provider,
    }


@router.post("/api/settings/demo")
async def toggle_demo_mode(request: DemoModeRequest) -> Dict[str, Any]:
    set_demo_mode(request.enabled)
    logger.info("Demo mode toggled to %s via API", request.enabled)
    return {"demo_mode": get_demo_mode()}
