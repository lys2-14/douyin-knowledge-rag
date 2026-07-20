"""
DashScope LLM provider (via DashScope SDK directly).
"""
from __future__ import annotations

from typing import Optional

from backend.llm.base import BaseLLM
from backend.config.settings import settings


class DashScopeLLM(BaseLLM):
    """DashScope (阿里云百炼) direct API."""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.model = model or settings.llm_model
        self.api_key = api_key or settings.dashscope_api_key or settings.llm_api_key or ""

    async def ask(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        import dashscope
        from http import HTTPStatus

        dashscope.api_key = self.api_key
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = dashscope.Generation.call(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            result_format="message",
        )

        if resp.status_code != HTTPStatus.OK:
            raise RuntimeError(f"DashScope LLM error: {resp.message}")

        return resp.output.choices[0].message.content

    async def ask_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        import dashscope
        from http import HTTPStatus

        dashscope.api_key = self.api_key
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        responses = dashscope.Generation.call(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            result_format="message",
            stream=True,
        )

        for resp in responses:
            if resp.status_code == HTTPStatus.OK:
                content = resp.output.choices[0].message.content
                if content:
                    yield content


__all__ = ["DashScopeLLM"]

