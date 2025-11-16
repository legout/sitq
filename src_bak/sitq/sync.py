"""
Synchronous wrapper around the async ``TaskQueue`` – useful for legacy code.
"""

import asyncio
from typing import Any, Callable, Dict, Optional

from .queue import TaskQueue
from .backends.base import Backend
from .serializers import Serializer
from .retry import RetryPolicy


class SyncTaskQueue:
    """
    Minimal sync façade.  It creates an event loop internally and forwards all
    calls to an underlying async ``TaskQueue``.
    """

    def __init__(
        self,
        backend: Backend,
        serializer: Serializer,
        retry_policy: Optional[RetryPolicy] = None,
        global_concurrency: int = 1000,
    ):
        self._backend = backend
        self._serializer = serializer
        self._queue_kwargs = {
            "retry_policy": retry_policy,
            "global_concurrency": global_concurrency,
        }
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._queue: Optional[TaskQueue] = None

    # ------------------------------------------------------------------
    def __enter__(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._queue = TaskQueue(self._backend, self._serializer, **self._queue_kwargs)
        self._loop.run_until_complete(self._queue.__aenter__())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._queue:
            self._loop.run_until_complete(
                self._queue.__aexit__(exc_type, exc_val, exc_tb)
            )
        if self._loop:
            self._loop.close()

    # ------------------------------------------------------------------
    def enqueue(
        self,
        func: Callable,
        *args,
        schedule: Optional[Dict] = None,
        max_retries: int = 3,
        retry_backoff: int = 1,
        **kwargs,
    ) -> str:
        if not self._queue:
            raise RuntimeError("SyncTaskQueue must be used inside a ``with`` block")
        return self._loop.run_until_complete(
            self._queue.enqueue(
                func,
                *args,
                schedule=schedule,
                max_retries=max_retries,
                retry_backoff=retry_backoff,
                **kwargs,
            )
        )

    def get_result(self, task_id: str, timeout: Optional[int] = None):
        if not self._queue:
            raise RuntimeError("SyncTaskQueue must be used inside a ``with`` block")
        return self._loop.run_until_complete(
            self._queue.get_result(task_id, timeout=timeout)
        )
