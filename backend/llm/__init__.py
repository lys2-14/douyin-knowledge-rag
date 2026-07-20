"""
LLM provider registry.
"""
from __future__ import annotations

from typing import Optional

from backend.config.settings import settings
from backend.llm.base import BaseLLM

_instances: dict[str, BaseLLM] = {}


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> BaseLLM:
    """Get or create an LLM instance by provider name."""
    provider = provider or settings.llm_provider
    key = f"{provider}::{model or settings.llm_model}"

    if key in _instances:
        return _instances[key]

    if provider == "openai":
        from backend.llm.openai import OpenAILLM
        inst = OpenAILLM(model=model)
    elif provider == "dashscope":
        from backend.llm.dashscope import DashScopeLLM
        inst = DashScopeLLM(model=model)
    elif provider == "ollama":
        from backend.llm.ollama import OllamaLLM
        inst = OllamaLLM(model=model)
    else:
        raise ValueError(f"Unknown LLM provider: {provider!r}")

    _instances[key] = inst
    return inst


__all__ = ["BaseLLM", "get_llm"]

