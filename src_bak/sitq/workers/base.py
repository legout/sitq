"""
Base worker – handles concurrency, locking, retries and context‑manager life‑cycle.
"""

from __future__ import annotations

import asyncio
import traceback
import uuid
from typing import Any, Callable, Set, Optional
import cloudpickle

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

        Notes on concurrency:
        - We fetch up to ``self.concurrency`` candidates to reduce backend round-trips.
        - For each claimed task we acquire the semaphore BEFORE launching the
          processing task and release it only after processing completes. This
          enforces the intended concurrency limit.
        """
        while self._running:
            due = await self.backend.fetch_due_tasks(limit=self.concurrency)
            if not due:
                await asyncio.sleep(0.1)
                continue

            for task in due:
                # Attempt to claim the task; if another worker grabbed it, skip.
                claimed = await self.backend.claim_task(task.id)
                if not claimed:
                    continue
                self._claimed_tasks.add(task.id)

                # Acquire semaphore BEFORE starting processing and ensure it's
                # released after processing finishes.
                await self.semaphore.acquire()
                asyncio.create_task(self._process_with_semaphore(task))

    # ------------------------------------------------------------------
    async def _process(self, task: Task):
        """
        Execute the task, store the result, and handle retry logic.
        Guarantees the lock is released exactly once.
        """
        try:
            # The queue now stores a single canonical envelope in Task.func.
            # Support both the old (separate func/args/kwargs) and new envelope
            # shapes for compatibility.
            payload = self.serializer.loads(task.func)
            if isinstance(payload, dict) and "func" in payload:
                func = payload["func"]
                args = tuple(payload.get("args", ())) if payload.get("args") is not None else ()
                kwargs = dict(payload.get("kwargs", {})) if payload.get("kwargs") is not None else {}
            else:
                func = payload
                args = self.serializer.loads(task.args) if task.args else ()
                kwargs = self.serializer.loads(task.kwargs) if task.kwargs else {}

            # Restore execution context (if present) and pass it to _execute so
            # subclasses can ensure the func runs inside the captured context.
            ctx = None
            if getattr(task, "context", None):
                try:
                    ctx = cloudpickle.loads(task.context)
                except Exception:
                    ctx = None

            result_value = await self._execute(func, *args, context=ctx, **kwargs)

            # Success → store result and mark task completed by setting result_id
            success_result = Result(
                task_id=task.id,
                status="success",
                value=self.serializer.dumps(result_value),
            )
            await self.backend.store_result(success_result)
            await self.backend.update_task_state(
                task.id,
                result_id=success_result.id,
                last_run_time=_now(),
            )

        except Exception as exc:
            tb = traceback.format_exc()
            # Decide if we should retry. IMPORTANT: do NOT write a non-terminal
            # failure result — only terminal failures should create final Result
            should_retry = (
                isinstance(exc, self.retry_policy.retry_on)
                and task.retries < task.max_retries
            )

            if should_retry:
                delay = self.retry_policy.get_delay(task.retries + 1)
                await self.backend.schedule_retry(task.id, delay)
            else:
                # Terminal failure → store final result and mark task completed
                failure_result = Result(
                    task_id=task.id,
                    status="failed",
                    traceback=tb,
                )
                await self.backend.store_result(failure_result)
                await self.backend.update_task_state(
                    task.id,
                    result_id=failure_result.id,
                    last_run_time=_now(),
                )

        finally:
            # Release lock (if we still hold it)
            if task.id in self._claimed_tasks:
                await self.backend.release_task(task.id)
                self._claimed_tasks.discard(task.id)

    # ------------------------------------------------------------------
    async def _process_with_semaphore(self, task: Task):
        """
        Helper wrapper that ensures the concurrency semaphore is released
        after the underlying processing finishes (regardless of outcome).
        """
        try:
            await self._process(task)
        finally:
            # Best effort: release the semaphore to avoid leaked permits if
            # something unexpected happens.
            try:
                self.semaphore.release()
            except Exception:
                # release should never raise in normal operation; swallow to
                # avoid crashing the worker loop.
                pass

    # ------------------------------------------------------------------
    async def _execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Sub‑classes implement the actual execution strategy.
        """
        raise NotImplementedError
