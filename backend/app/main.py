import logging
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routes.chat import router as chat_router
from app.routes.health import router as health_router
from app.routes.sales import router as sales_router
from app.routes.settings import router as settings_router
from app.services.ingestion import run_ingestion
from app.services.vector_store import get_vector_store


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    _configure_logging(settings.log_level)
    logger = logging.getLogger(__name__)
    logger.info("MarketMate API starting up")

    try:
        vs = get_vector_store()
        doc_count = vs.document_count()
        logger.info("ChromaDB connected: %d documents indexed", doc_count)

        if doc_count == 0:
            logger.info("Collection empty - running ingestion from %s", settings.sales_data_path)
            ingested = run_ingestion(vs, settings.sales_data_path)
            logger.info("Ingestion complete: %d documents", ingested)
        else:
            logger.info("Collection already populated - skipping ingestion")
    except Exception as exc:
        logger.error("Startup error during ingestion: %s", exc, exc_info=True)

    yield

    logger.info("MarketMate API shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="MarketMate API",
        version="1.0.0",
        description="AI ordering assistant for Melbourne fresh produce retailers",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(sales_router)
    app.include_router(settings_router)

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next: Any) -> Any:
        logger = logging.getLogger("marketmate.access")
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        logger.info(
            "%s %s %d %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger = logging.getLogger("marketmate.errors")
        logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error": str(exc)},
        )

    return app


app = create_app()
