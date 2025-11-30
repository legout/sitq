"""
Async TaskQueue implementation for enqueueing and retrieving task results.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from .serialization import Serializer, CloudpickleSerializer
from .backends.base import Backend
from .result import Result


class TaskQueue:
    """
    Async task queue for enqueueing tasks and retrieving results.

    Args:
        backend: Backend implementation for task persistence
        serializer: Serializer for task payloads and results.
                   Defaults to CloudpickleSerializer.
    """

    def __init__(
        self,
        backend: Optional[Backend] = None,
        serializer: Optional[Serializer] = None,
        default_result_timeout: Optional[float] = None,
    ):
        # Provide defaults if not specified
        if backend is None:
            from .backends.sqlite import SQLiteBackend

            backend = SQLiteBackend(":memory:")  # Default in-memory SQLite

        if serializer is None:
            serializer = CloudpickleSerializer()

        self.backend = backend
        self.serializer = serializer
        self.default_result_timeout = default_result_timeout

    async def enqueue(
        self,
        func: Any,
        *args: Any,
        eta: Optional[datetime] = None,
        context: Optional[dict] = None,
        **kwargs: Any,
    ) -> str:
        """
        Enqueue a task for execution.

        Args:
            func: Callable to execute
            *args: Positional arguments for the callable
            eta: Optional execution time. If None, task is available immediately.
            **kwargs: Keyword arguments for the callable

        Returns:
            str: Task ID for result retrieval
        """
        # Generate unique task ID
        task_id = str(uuid.uuid4())

        # Create task payload
        payload = {"func": func, "args": args, "kwargs": kwargs}
        if context is not None:
            payload["context"] = context

        # Serialize payload
        serialized_payload = self.serializer.dumps(payload)

        # Determine availability time
        if eta is None:
            available_at = datetime.now(timezone.utc)
        else:
            available_at = eta

        # Store task in backend
        await self.backend.enqueue(task_id, serialized_payload, available_at)

        return task_id

    async def get_result(
        self, task_id: str, timeout: Optional[float] = None
    ) -> Optional[Result]:
        """
        Retrieve the result of a completed task.

        Args:
            task_id: ID of the task to retrieve result for
            timeout: Optional timeout in seconds

        Returns:
            Result: Result object if task completed, None if not ready or timeout

        Raises:
            KeyError: If task ID is not found
        """

        async def _get_result():
            backend_result = await self.backend.get_result(task_id)
            if backend_result is None:
                return None

            # Convert backend Result to public Result
            # Deserialize result value if present
            value = backend_result.value
            if value is not None:
                value = self.serializer.loads(value)

            return Result(
                task_id=backend_result.task_id,
                status=backend_result.status,
                value=value,
                error=backend_result.error,
                traceback=backend_result.traceback,
                enqueued_at=backend_result.enqueued_at,
                finished_at=backend_result.finished_at,
            )

        # Use default_result_timeout if no explicit timeout provided
        if timeout is None:
            timeout = self.default_result_timeout

        if timeout is None:
            return await _get_result()

        try:
            return await asyncio.wait_for(_get_result(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def close(self) -> None:
        """
        Close the task queue and cleanup resources.
        """
        await self.backend.close()

    async def __aenter__(self) -> "TaskQueue":
        """Async context manager entry."""
        await self.backend.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
