"""
OpenAI-compatible LLM provider.
"""
from __future__ import annotations

from typing import Optional
from openai import AsyncOpenAI

from backend.llm.base import BaseLLM
from backend.config.settings import settings


class OpenAILLM(BaseLLM):
    """Works with any OpenAI-compatible API (OpenAI, DashScope, DeepSeek, etc.)."""

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.model = model or settings.llm_model
        import httpx
        proxies = {}
        if settings.http_proxy:
            proxies["http://"] = settings.http_proxy
            proxies["https://"] = settings.https_proxy or settings.http_proxy
        client_kwargs = {}
        if proxies:
            client_kwargs["http_client"] = httpx.AsyncClient(proxies=proxies)
        self._client = AsyncOpenAI(
            base_url=base_url or settings.llm_base_url or "https://api.openai.com/v1",
            api_key=api_key or settings.llm_api_key or "",
            **client_kwargs,
        )

    async def ask(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""

    async def ask_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content


__all__ = ["OpenAILLM"]

