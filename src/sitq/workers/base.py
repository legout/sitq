"""
Base worker – handles concurrency, locking, retries and context‑manager life‑cycle.
"""

from __future__ import annotations

import asyncio
import traceback
import uuid
from typing import Any, Callable, Set, Optional

from ..core import Task, Result, _now
from ..backends.base import Backend
from ..serializers import Serializer
from ..retry import RetryPolicy


class Worker:
    """
    Abstract worker that knows how to claim a task, execute it, store the result,
    and optionally retry on failure.
    """

    def __init__(
        self,
        backend: Backend,
        serializer: Serializer,
        concurrency: int = 10,
        retry_policy: Optional[RetryPolicy] = None,
    ):
        self.backend = backend
        self.serializer = serializer
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)
        self.retry_policy = retry_policy or RetryPolicy()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._claimed_tasks: Set[str] = set()

    # ------------------------------------------------------------------
    # Async context‑manager support
    # ------------------------------------------------------------------
    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.stop()

    async def start(self):
        self._running = True
        self._worker_task = asyncio.create_task(self._run())

    async def stop(self):
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        # Defensive release of any locks we still hold
        for tid in list(self._claimed_tasks):
            await self.backend.release_task(tid)
        self._claimed_tasks.clear()

    # ------------------------------------------------------------------
    async def _run(self):
        """
        Main loop – fetches tasks, claims them atomically, then processes them
        while respecting the concurrency semaphore.
        """
        while self._running:
            async with self.semaphore:
                due = await self.backend.fetch_due_tasks(limit=1)
                if not due:
                    await asyncio.sleep(0.1)
                    continue
                task = due[0]

                # Attempt to claim the task; if another worker grabbed it, skip.
                claimed = await self.backend.claim_task(task.id)
                if not claimed:
                    continue
                self._claimed_tasks.add(task.id)

                # Fire‑and‑forget processing (so the semaphore can be released)
                asyncio.create_task(self._process(task))

    # ------------------------------------------------------------------
    async def _process(self, task: Task):
        """
        Execute the task, store the result, and handle retry logic.
        Guarantees the lock is released exactly once.
        """
        try:
            func = self.serializer.loads(task.func)
            args = self.serializer.loads(task.args) if task.args else ()
            kwargs = self.serializer.loads(task.kwargs) if task.kwargs else {}

            result_value = await self._execute(func, *args, **kwargs)

            # Success → store result
            await self.backend.store_result(
                Result(
                    task_id=task.id,
                    status="success",
                    value=self.serializer.dumps(result_value),
                )
            )
            await self.backend.update_task_state(task.id, last_run_time=_now())

        except Exception as exc:
            tb = traceback.format_exc()
            # Record the failure (may be overwritten on a later retry)
            await self.backend.store_result(
                Result(
                    task_id=task.id,
                    status="failed",
                    traceback=tb,
                )
            )

            # Decide if we should retry
            if (
                isinstance(exc, self.retry_policy.retry_on)
                and task.retries < task.max_retries
            ):
                delay = self.retry_policy.get_delay(task.retries + 1)
                await self.backend.schedule_retry(task.id, delay)
            # else: give up – failure already stored

        finally:
            # Release lock (if we still hold it)
            if task.id in self._claimed_tasks:
                await self.backend.release_task(task.id)
                self._claimed_tasks.discard(task.id)

    # ------------------------------------------------------------------
    async def _execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Sub‑classes implement the actual execution strategy.
        """
        raise NotImplementedError
