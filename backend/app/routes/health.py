import logging
from typing import Dict, Any

from fastapi import APIRouter

from app.config import get_settings
from app.services.vector_store import get_vector_store


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    settings = get_settings()

    try:
        vs = get_vector_store()
        doc_count = vs.document_count()
    except Exception as exc:
        logger.warning("Health check: vector store unavailable: %s", exc)
        doc_count = 0

    return {
        "status": "ok",
        "demo_mode": settings.demo_mode,
        "documents_indexed": doc_count,
        "model": settings.llm_model,
    }
