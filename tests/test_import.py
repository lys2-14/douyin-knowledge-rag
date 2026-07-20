"""Test that all modules can be imported."""
from __future__ import annotations


def test_import_base_provider() -> None:
    """Test base provider import."""
    from backend.providers.base import BaseProvider, UserInfo, FolderInfo, VideoInfo
    assert BaseProvider is not None
    assert UserInfo is not None
    assert FolderInfo is not None
    assert VideoInfo is not None


def test_import_pipeline() -> None:
    """Test pipeline modules import."""
    from backend.pipeline import build_sync_pipeline
    from backend.pipeline.base import Pipeline, PipelineContext, StageStatus
    assert build_sync_pipeline is not None
    assert Pipeline is not None
    assert PipelineContext is not None
    assert StageStatus is not None


def test_import_rag() -> None:
    """Test RAG modules import."""
    from backend.rag.chain import RAGChain
    from backend.rag.retriever import Retriever
    assert RAGChain is not None
    assert Retriever is not None


def test_import_llm() -> None:
    """Test LLM modules import."""
    from backend.llm import get_llm
    from backend.llm.base import BaseLLM
    assert get_llm is not None
    assert BaseLLM is not None


def test_import_embedding() -> None:
    """Test embedding modules import."""
    from backend.embedding import get_embedding
    from backend.embedding.base import BaseEmbedding
    assert get_embedding is not None
    assert BaseEmbedding is not None


def test_import_config() -> None:
    """Test settings import."""
    from backend.config.settings import settings
    assert settings is not None
    assert hasattr(settings, "app_name")
