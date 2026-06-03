import logging
from typing import Optional

logger = logging.getLogger(__name__)

_demo_mode_override: Optional[bool] = None


def get_demo_mode() -> bool:
    if _demo_mode_override is not None:
        return _demo_mode_override
    from app.config import get_settings
    return get_settings().demo_mode


def set_demo_mode(enabled: bool) -> None:
    global _demo_mode_override
    _demo_mode_override = enabled
    logger.info("Demo mode set to %s at runtime", enabled)
