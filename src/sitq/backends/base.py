"""
Backend protocol and data models for queue persistence.
"""

from dataclasses import dataclass
from typing import Protocol, List, Optional, Any
from datetime import datetime


@dataclass
class ReservedTask:
    """
    Data model for tasks that have been reserved by a worker for execution.
    """
    task_id: str
    payload: bytes
    started_at: datetime


@dataclass 
class Result:
    """
    Data model for completed task results.
    """
    task_id: str
    status: str  # 'success' or 'failure'
    value: Optional[Any] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    finished_at: Optional[datetime] = None


class Backend(Protocol):
    """
    Protocol for backend implementations that persist tasks and results.

    Backends are responsible for:
    - Storing tasks with payloads and metadata
    - Atomic task reservation for workers
    - Recording task results and status
    - Retrieving completed task results
    """

    async def enqueue(
        self,
        task_id: str,
        payload: bytes,
        available_at: datetime
    ) -> None:
        """
        Persist a new task with pending status.

        Args:
            task_id: Unique identifier for the task
            payload: Serialized task payload
            available_at: Time when task becomes available for execution
        """
        ...

    async def reserve(
        self,
        max_items: int,
        now: datetime
    ) -> List[ReservedTask]:
        """
        Atomically reserve tasks for execution by workers.

        Args:
            max_items: Maximum number of tasks to reserve
            now: Current time for availability check

        Returns:
            List of ReservedTask instances for reserved tasks
        """
        ...

    async def mark_success(
        self,
        task_id: str,
        value: Any,
        finished_at: datetime
    ) -> None:
        """
        Mark a task as successfully completed.

        Args:
            task_id: Identifier of the completed task
            value: Result value to store
            finished_at: Time when task finished
        """
        ...

    async def mark_failure(
        self,
        task_id: str,
        error: str,
        traceback: Optional[str],
        finished_at: datetime
    ) -> None:
        """
        Mark a task as failed.

        Args:
            task_id: Identifier of the failed task
            error: Error message
            traceback: Optional error traceback
            finished_at: Time when task failed
        """
        ...

    async def get_result(self, task_id: str) -> Optional[Result]:
        """
        Retrieve the result of a completed task.

        Args:
            task_id: Identifier of the task to retrieve result for

        Returns:
            Result object if task completed, None otherwise
        """
        ...

    async def close(self) -> None:
        """
        Close backend connections and cleanup resources.
        """
        ...
