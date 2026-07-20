"""
Ollama LLM provider (local models).
"""
from __future__ import annotations

from typing import Optional
import httpx

from backend.llm.base import BaseLLM
from backend.config.settings import settings


class OllamaLLM(BaseLLM):
    """Local Ollama instance."""

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model or settings.llm_model or "qwen2.5:7b"
        self.base_url = (base_url or settings.llm_base_url or
                         "http://localhost:11434").rstrip("/")

    async def ask(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system or "",
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        async with httpx.AsyncClient(timeout=120) as cli:
            resp = await cli.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data.get("response", "")

    async def ask_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system or "",
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        async with httpx.AsyncClient(timeout=300) as cli:
            async with cli.stream("POST", f"{self.base_url}/api/generate",
                                  json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.strip():
                        import json as _json
                        data = _json.loads(line)
                        token = data.get("response", "")
                        if token:
                            yield token


__all__ = ["OllamaLLM"]

