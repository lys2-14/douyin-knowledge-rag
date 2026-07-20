from backend.pipeline.base import Pipeline, PipelineStage, PipelineContext, StageStatus
from backend.pipeline.download import AudioDownloadStage
from backend.pipeline.transcribe import ASRStage
from backend.pipeline.summarize import SummarizeStage
from backend.pipeline.chunk import ChunkStage
from backend.pipeline.embed import EmbeddingStage


def build_sync_pipeline() -> Pipeline:
    """Standard pipeline for syncing a single video."""
    return Pipeline(stages=[
        AudioDownloadStage(),
        ASRStage(),
        SummarizeStage(),
        ChunkStage(),
        EmbeddingStage(),
    ])


__all__ = [
    "Pipeline", "PipelineStage", "PipelineContext", "StageStatus",
    "AudioDownloadStage", "ASRStage", "SummarizeStage",
    "ChunkStage", "EmbeddingStage",
    "build_sync_pipeline",
]

