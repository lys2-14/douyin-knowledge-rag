"""
FastAPI application factory.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from backend.config.settings import settings, ensure_directories
from backend.storage.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"棣冩畬 {settings.app_name} starting...")
    ensure_directories()
    await init_db()
    logger.info("[OK]  Database ready")
    _check_config_warnings()
    yield
    logger.info("Shutdown")
    logger.info("棣冩啟 Shutdown")







def _check_config_warnings() -> None:
    """Check common configuration issues at startup."""
    from backend.config.settings import settings
    import shutil
    key = settings.llm_api_key or settings.dashscope_api_key or ""
    if not key or key in ("YOUR_API_KEY_HERE", "YOUR_DASHSCOPE_KEY_HERE"):
        print("WARNING: LLM_API_KEY not configured!")
    if shutil.which("ffmpeg") is None:
        print("WARNING: ffmpeg not found!")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="""
Collect, process and chat with your favourite videos.

## Providers
- Douyin (閹舵牠鐓?
- More coming閳?
## Pipeline
Download 閳?ASR 閳?Summarize 閳?Chunk 閳?Embed 閳?Vector Store

## RAG
Retrieval-Augmented Generation with multi-model support.
        """,
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG" if settings.debug else "INFO",
    )
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
    )

    # Register routers
    from backend.api.routes import auth, favorites, knowledge, chat, export
    app.include_router(auth.router)
    app.include_router(favorites.router)
    app.include_router(knowledge.router)
    app.include_router(chat.router)
    app.include_router(export.router)

    @app.get("/")
    async def root():
        return {
            "message": f"棣冩憥 {settings.app_name}",
            "version": "0.1.0",
            "docs": "/docs",
            "providers": ["douyin"],
        }

    @app.get("/health")
    async def health():
        return {"status": "healthy"}


    @app.get("/api/config/check")
    async def config_check():
        """Check system configuration."""
        return {"status": "ok", "message": "config check placeholder"}

    return app


__all__ = ["create_app"]




