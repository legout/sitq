"""
Abstract backend definition – all concrete back‑ends inherit from this.
"""

from __future__ import annotations

import abc
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core import Task, Result
from ..serializers import Serializer


class Backend(abc.ABC):
    """Base class for all back‑ends. Implements async context‑manager protocol."""

    # ------------------------------------------------------------------
    # Lifecycle helpers (connect / close)
    # ------------------------------------------------------------------
    async def __aenter__(self) -> "Backend":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover
        await self.close()

    @abc.abstractmethod
    async def connect(self) -> None:
        """Open any required connections (DB, network, etc.)."""
        ...

    @abc.abstractmethod
    async def close(self) -> None:
        """Close / clean up all resources."""
        ...

    # ------------------------------------------------------------------
    # Core task operations
    # ------------------------------------------------------------------
    @abc.abstractmethod
    async def enqueue(self, task: Task) -> None:
        """Persist a new task."""
        ...

    @abc.abstractmethod
    async def fetch_due_tasks(self, limit: int = 1) -> List[Task]:
        """
        Return up to ``limit`` tasks that are ready to run.
        Implementations must ensure the tasks are *not* already claimed.
        """
        ...

    @abc.abstractmethod
    async def update_task_state(self, task_id: str, **kwargs) -> None:
        """Patch a task row (e.g. ``next_run_time``, ``retries``)."""
        ...

    @abc.abstractmethod
    async def store_result(self, result: Result) -> None:
        """Persist a task result."""
        ...

    @abc.abstractmethod
    async def get_result(self, task_id: str) -> Optional[Result]:
        """Retrieve the result for ``task_id`` (None if not ready)."""
        ...

    # ------------------------------------------------------------------
    # Distributed coordination helpers
    # ------------------------------------------------------------------
    @abc.abstractmethod
    async def claim_task(self, task_id: str, lock_timeout: int = 30) -> bool:
        """
        Atomically claim a task for processing.
        Returns ``True`` when the lock was acquired.
        """
        ...

    @abc.abstractmethod
    async def release_task(self, task_id: str) -> None:
        """Release the lock for ``task_id`` (called when a worker aborts)."""
        ...

    @abc.abstractmethod
    async def schedule_retry(self, task_id: str, delay: int) -> None:
        """Reschedule a failed task after ``delay`` seconds and bump retry counter."""
        ...
