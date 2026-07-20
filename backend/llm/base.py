"""
Abstract LLM interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class BaseLLM(ABC):
    """Interface every LLM provider implements."""

    @abstractmethod
    async def ask(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        ...

    @abstractmethod
    async def ask_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        """Async generator yielding string tokens."""
        ...


__all__ = ["BaseLLM"]

