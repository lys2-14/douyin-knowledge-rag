"""
Async task definitions (pluggable worker backend).

Currently uses asyncio.create_task.  Can be swapped for Celery / RQ / Arq later.
"""
from __future__ import annotations

import asyncio
from typing import Callable


class TaskQueue:
    """Minimal in-process async task queue."""

    def __init__(self, concurrency: int = 2):
        self.concurrency = concurrency
        self._semaphore = asyncio.Semaphore(concurrency)
        self._tasks: list[asyncio.Task] = []

    async def enqueue(self, fn: Callable, *args, **kwargs):
        async with self._semaphore:
            task = asyncio.create_task(fn(*args, **kwargs))
            self._tasks.append(task)
            return await task

    def enqueue_background(self, fn: Callable, *args, **kwargs):
        """Fire and forget."""
        task = asyncio.create_task(self._run_with_semaphore(fn, *args, **kwargs))
        self._tasks.append(task)
        return task

    async def _run_with_semaphore(self, fn, *args, **kwargs):
        async with self._semaphore:
            await fn(*args, **kwargs)

    async def wait_all(self):
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)


# Global queue
_queue: TaskQueue | None = None


def get_task_queue(concurrency: int = 2) -> TaskQueue:
    global _queue
    if _queue is None:
        _queue = TaskQueue(concurrency=concurrency)
    return _queue


__all__ = ["TaskQueue", "get_task_queue"]

