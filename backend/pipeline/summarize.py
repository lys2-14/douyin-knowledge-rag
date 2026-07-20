"""
LLM-based summarisation stage.
"""
from __future__ import annotations

from backend.pipeline.base import PipelineStage, PipelineContext, StageStatus
from backend.llm import get_llm
from backend.rag.prompt import SUMMARY_PROMPT


class SummarizeStage(PipelineStage):
    """Generate a concise summary of the video content."""

    def __init__(self, model: str | None = None):
        super().__init__("summarize")
        self._model = model

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        source_text = (ctx.transcript or "") + "\n\n" + (ctx.description or "") + "\n\n" + (ctx.title or "")
        if not source_text.strip() or len(source_text.strip()) < 10:
            ctx.stage_statuses[self.name] = StageStatus.SKIPPED
            return ctx

        llm = get_llm(model=self._model)
        prompt = SUMMARY_PROMPT.format(
            title=ctx.title,
            author=ctx.author_name,
            content=source_text[:8000],  # truncate for token limits
        )
        ctx.summary = await llm.ask(prompt)
        return ctx


__all__ = ["SummarizeStage"]

