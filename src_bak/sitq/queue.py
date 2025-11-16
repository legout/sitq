"""
High‑level async API that applications use to enqueue tasks and retrieve results.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import uuid
import contextvars
import cloudpickle

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
        Serialize ``func`` and its arguments into the canonical envelope and
        persist a ``Task``.

        Canonical envelope shape:
            {
                "func": <callable or import-path-string>,
                "args": <positional args tuple/list>,
                "kwargs": <keyword args dict>
            }

        Note: the envelope is stored in ``Task.func`` as a single serialized blob.
        This keeps backends simpler (they store a single payload) and ensures a
        consistent contract across transports.
        """
        envelope = {"func": func, "args": args or (), "kwargs": kwargs or {}}

        # Capture current execution context (contextvars) at enqueue time and
        # serialize it with cloudpickle. We store it on the Task so backends can
        # persist and workers can restore it before execution.
        try:
            ctx = contextvars.copy_context()
            ctx_bytes = cloudpickle.dumps(ctx)
        except Exception:
            ctx_bytes = None

        task = Task(
            id=str(uuid.uuid4()),
            func=self.serializer.dumps(envelope),
            args=None,
            kwargs=None,
            context=ctx_bytes,
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
