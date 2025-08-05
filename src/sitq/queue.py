"""
High‑level async API that applications use to enqueue tasks and retrieve results.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import uuid

from .core import Task, Result, _now
from .backends.base import Backend
from .serializers import Serializer
from .retry import RetryPolicy


class TaskQueue:
    """
    Public façade – enqueues tasks, optionally starts a background scheduler,
    and provides a simple ``get_result`` poller.
    """

    def __init__(
        self,
        backend: Backend,
        serializer: Serializer,
        retry_policy: Optional[RetryPolicy] = None,
        global_concurrency: int = 1000,
    ):
        self.backend = backend
        self.serializer = serializer
        self.retry_policy = retry_policy or RetryPolicy()
        self.global_concurrency = global_concurrency
        self._inflight = 0
        self._inflight_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    async def __aenter__(self):
        await self.backend.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.backend.__aexit__(exc_type, exc, tb)

    # ------------------------------------------------------------------
    async def enqueue(
        self,
        func: Callable,
        *args,
        schedule: Optional[Dict] = None,
        max_retries: int = 3,
        retry_backoff: int = 1,
        **kwargs,
    ) -> str:
        """
        Serialize ``func`` and its arguments, build a ``Task`` and persist it.
        """
        task = Task(
            id=str(uuid.uuid4()),
            func=self.serializer.dumps(func),
            args=self.serializer.dumps(args) if args else None,
            kwargs=self.serializer.dumps(kwargs) if kwargs else None,
            schedule=schedule,
            max_retries=max_retries,
            retry_backoff=retry_backoff,
        )
        await self.backend.enqueue(task)
        return task.id

    # ------------------------------------------------------------------
    async def get_result(
        self, task_id: str, timeout: Optional[int] = None
    ) -> Optional[Result]:
        """
        Poll for a result until it becomes available or ``timeout`` seconds
        elapse. Returns ``None`` on timeout.
        """
        start = _now()
        while True:
            result = await self.backend.get_result(task_id)
            if result:
                return result
            if timeout and (_now() - start).total_seconds() > timeout:
                return None
            await asyncio.sleep(0.5)

    # ------------------------------------------------------------------
    async def start_scheduler(self, poll_interval: float = 1.0):
        """
        Some back‑ends (Redis, NATS) expose a private helper that moves due
        scheduled tasks to the immediate queue.  This method simply forwards
        the call if it exists.
        """
        if hasattr(self.backend, "_move_due_scheduled"):
            await self.backend._move_due_scheduled(poll_interval)
