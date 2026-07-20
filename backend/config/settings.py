"""
Global configuration via environment variables + .env
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────
    app_name: str = "Knowledge RAG"
    app_host: str = Field(default="0.0.0.0", env="APP_HOST")
    app_port: int = Field(default=8000, env="APP_PORT")
    debug: bool = Field(default=False, env="DEBUG")

    # ── Default provider ─────────────────────────────────────────────
    provider: str = Field(default="douyin", env="PROVIDER")

    # ── LLM ──────────────────────────────────────────────────────────
    llm_provider: str = Field(default="dashscope", env="LLM_PROVIDER")
    llm_model: str = Field(default="qwen-plus", env="LLM_MODEL")
    llm_base_url: Optional[str] = Field(default=None, env="LLM_BASE_URL")
    llm_api_key: Optional[str] = Field(default=None, env="LLM_API_KEY")

    # ── Embedding ────────────────────────────────────────────────────
    embedding_provider: str = Field(default="dashscope", env="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="text-embedding-v3", env="EMBEDDING_MODEL")
    embedding_base_url: Optional[str] = Field(default=None, env="EMBEDDING_BASE_URL")
    embedding_api_key: Optional[str] = Field(default=None, env="EMBEDDING_API_KEY")
    embedding_dimensions: int = Field(default=1024, env="EMBEDDING_DIMENSIONS")

    # ── Vector Store ─────────────────────────────────────────────────
    vector_backend: str = Field(default="chroma", env="VECTOR_BACKEND")
    chroma_persist_dir: str = Field(
        default="./data/chroma_db", env="CHROMA_PERSIST_DIRECTORY"
    )

    # ── ASR ──────────────────────────────────────────────────────────
    asr_provider: str = Field(default="dashscope", env="ASR_PROVIDER")
    asr_model: str = Field(default="paraformer-v2", env="ASR_MODEL")
    asr_timeout: int = Field(default=600, env="ASR_TIMEOUT")

    # ── DashScope (legacy alias convenience) ─────────────────────────
    dashscope_api_key: Optional[str] = Field(default=None, env="DASHSCOPE_API_KEY")
    dashscope_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/api/v1", env="DASHSCOPE_BASE_URL"
    )

    # ── Database ─────────────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/knowledge_rag.db", env="DATABASE_URL"
    )

    # ── Retrieval ────────────────────────────────────────────────────
    retrieval_candidate_k: int = Field(default=24, env="RETRIEVAL_CANDIDATE_K")
    retrieval_top_k: int = Field(default=8, env="RETRIEVAL_TOP_K")
    retrieval_mmr_fetch_k: int = Field(default=32, env="RETRIEVAL_MMR_FETCH_K")
    retrieval_mmr_lambda: float = Field(default=0.55, env="RETRIEVAL_MMR_LAMBDA")
    retrieval_score_threshold: float = Field(default=0.0, env="RETRIEVAL_SCORE_THRESHOLD")

    # ── Worker ───────────────────────────────────────────────────────
    worker_concurrency: int = Field(default=2, env="WORKER_CONCURRENCY")
    worker_backend: str = Field(default="thread", env="WORKER_BACKEND")
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")

    # ── Chunk ────────────────────────────────────────────────────────
    chunk_strategy: str = Field(default="semantic", env="CHUNK_STRATEGY")
    chunk_size: int = Field(default=512, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=64, env="CHUNK_OVERLAP")

    # ── Project paths ────────────────────────────────────────────────

    # Proxy (for OpenAI in China)
    http_proxy: Optional[str] = Field(default=None, env="HTTP_PROXY")
    https_proxy: Optional[str] = Field(default=None, env="HTTPS_PROXY")
    project_root: Path = Path(__file__).resolve().parent.parent.parent

    @field_validator("dashscope_api_key")
    @classmethod
    def _fallback_api_key(cls, v: str | None, info) -> str | None:
        """If DASHSCOPE_API_KEY is unset, fall back to LLM_API_KEY."""
        if v:
            return v
        return info.data.get("llm_api_key") or None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()


def ensure_directories() -> None:
    import os
    hf = os.environ.get('HF_ENDPOINT') or os.environ.get('_HF_ENDPOINT') or ''
    if hf: os.environ.setdefault('HF_ENDPOINT', hf)
    """Create required runtime directories."""
    import os
    for d in [
        "data",
        settings.chroma_persist_dir,
        "logs",
        "cache/audio",
        "cache/transcript",
        "cache/thumbnails",
    ]:
        os.makedirs(d, exist_ok=True)


__all__ = ["settings", "ensure_directories"]


