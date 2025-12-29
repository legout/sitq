"""Abstract backend definition for sitq."""

from __future__ import annotations

__all__ = ["Backend"]

import abc
from datetime import datetime
from typing import List, Optional

from ..core import Task, Result, ReservedTask


class Backend(abc.ABC):
    """Base class for all backends. Implements async context-manager protocol."""

    # ------------------------------------------------------------------
    # Lifecycle helpers (connect / close)
    # ------------------------------------------------------------------
    async def __aenter__(self) -> "Backend":
        """
        Async context manager entry point.

        Returns:
            The backend instance.

        Raises:
            BackendError: If connection fails.
        """
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """
        Async context manager exit point.

        Args:
            exc_type: Exception type if an exception occurred.
            exc: Exception instance if an exception occurred.
            tb: Traceback if an exception occurred.

        Returns:
            None
        """
        await self.close()

    @abc.abstractmethod
    async def connect(self) -> None:
        """
        Open any required connections (DB, network, etc.).

        Returns:
            None

        Raises:
            BackendError: If connection fails.
        """
        ...

    @abc.abstractmethod
    async def close(self) -> None:
        """
        Close / clean up all resources.

        Returns:
            None

        Raises:
            BackendError: If cleanup fails.
        """
        ...

    # ------------------------------------------------------------------
    # Core task operations
    # ------------------------------------------------------------------
    @abc.abstractmethod
    async def enqueue(self, task: Task) -> None:
        """
        Persist a new task.

        Args:
            task: The task object to persist.

        Returns:
            None

        Raises:
            BackendError: If the task cannot be persisted.
        """
        ...

    @abc.abstractmethod
    async def reserve(self, max_items: int, now: datetime) -> List[ReservedTask]:
        """
        Reserve up to ``max_items`` tasks that are ready to run.

        Args:
            max_items: Maximum number of tasks to reserve.
            now: Current datetime for comparison with task availability.

        Returns:
            ReservedTask instances for successfully reserved tasks.

        Raises:
            BackendError: If reservation fails.
        """
        ...

    @abc.abstractmethod
    async def mark_success(self, task_id: str, result_value: bytes) -> None:
        """
        Mark a task as successfully completed.

        Args:
            task_id: The ID of the task to mark as successful.
            result_value: The serialized result value to store.

        Returns:
            None

        Raises:
            BackendError: If marking success fails.
        """
        ...

    @abc.abstractmethod
    async def mark_failure(self, task_id: str, error: str, traceback: str) -> None:
        """
        Mark a task as failed.

        Args:
            task_id: The ID of the task to mark as failed.
            error: The error message describing the failure.
            traceback: The full traceback of the exception.

        Returns:
            None

        Raises:
            BackendError: If marking failure fails.
        """
        ...

    @abc.abstractmethod
    async def get_result(self, task_id: str) -> Optional[Result]:
        """
        Retrieve the result for ``task_id`` (None if not ready).

        Args:
            task_id: The ID of the task to retrieve the result for.

        Returns:
            The Result object if available, None if task is not complete.

        Raises:
            BackendError: If retrieval fails.
        """
        ...

    # ------------------------------------------------------------------
    # Legacy compatibility methods (can be implemented using new methods)
    # ------------------------------------------------------------------
    async def fetch_due_tasks(self, limit: int = 1) -> List[Task]:
        """
        Return up to ``limit`` tasks that are ready to run.
        Legacy method - can be implemented using reserve().
        """
        # Default implementation using reserve() for compatibility
        reserved_tasks = await self.reserve(limit, datetime.now())
        # Convert ReservedTask back to Task for compatibility
        return [
            Task(id=rt.task_id, func=rt.func, context=rt.context)
            for rt in reserved_tasks
        ]

    async def update_task_state(self, task_id: str, **kwargs) -> None:
        """Patch a task row (e.g. ``next_run_time``, ``retries``)."""
        # Default implementation for compatibility
        pass

    async def store_result(self, result: Result) -> None:
        """Persist a task result."""
        # Default implementation for compatibility
        pass

    async def claim_task(self, task_id: str, lock_timeout: int = 30) -> bool:
        """
        Atomically claim a task for processing.
        Legacy method - can be implemented using reserve().
        """
        # Default implementation for compatibility
        return True

    async def release_task(self, task_id: str) -> None:
        """Release the lock for ``task_id`` (called when a worker aborts)."""
        # Default implementation for compatibility
        pass

    async def schedule_retry(self, task_id: str, delay: int) -> None:
        """Reschedule a failed task after ``delay`` seconds and bump retry counter."""
        # Default implementation for compatibility
        pass
