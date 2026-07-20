"""Test configuration loading."""
from __future__ import annotations

import os


def test_settings_defaults() -> None:
    """Test settings can be loaded with defaults."""
    from backend.config.settings import settings
    assert settings.app_name == "Knowledge RAG"
    assert settings.app_host == "0.0.0.0"
    assert isinstance(settings.app_port, int)
    assert settings.vector_backend == "chroma"


def test_settings_from_env(monkeypatch) -> None:
    """Test settings pick up environment variables."""
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("APP_PORT", "9999")
    # Reload settings with new env (import again)
    import importlib
    from backend.config import settings as settings_module
    importlib.reload(settings_module)
    from backend.config.settings import settings
    # Check that env vars were picked up
    assert settings.app_port == 9999

    # Cleanup
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("APP_PORT", raising=False)
