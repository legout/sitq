"""Task queue implementation for sitq."""

from __future__ import annotations

__all__ = ["TaskQueue"]

import asyncio
from datetime import datetime
from typing import Optional, Any

from .serialization import Serializer, CloudpickleSerializer
from .core import Task, Result, _now
from .backends.base import Backend
from .exceptions import (
    TaskQueueError,
    ValidationError,
    TimeoutError,
    SerializationError,
)
from .validation import (
    validate,
    validate_callable,
    validate_non_empty_string,
    validate_non_negative_number,
    validate_timezone_aware_datetime,
)


class TaskQueue:
    """Async task queue for enqueuing background jobs and retrieving results.

    This class provides the primary interface for enqueuing tasks and retrieving
    their results. It manages task persistence through a backend and handles
    serialization using the configured serializer.

    Attributes:
        backend: Backend instance for task persistence.
        serializer: Serializer instance for task/result serialization.
        _initialized: Whether the queue has been initialized.

    Example:
        >>> backend = SQLiteBackend("tasks.db")
        >>> queue = TaskQueue(backend=backend)
        >>> task_id = await queue.enqueue(my_function, arg1, arg2)
        >>> result = await queue.get_result(task_id)

    See Also:
        Worker: For processing enqueued tasks
        SyncTaskQueue: For synchronous usage in non-async contexts
        SQLiteBackend: For SQLite-based task persistence
        Task: For task data structure
        Result: For task result handling
    """
        # Input validation
        validate(backend, "backend").is_required().validate()
        
        if serializer is not None:
            validate(serializer, "serializer").is_callable().validate()
        
        self.backend = backend

    async def __aenter__(self):
        """Enter async context manager and connect to backend.

        Returns:
            TaskQueue: The task queue instance.

        Raises:
            BackendError: If backend connection fails.
        """
        await self.backend.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Exit async context manager and close backend connection.

        Args:
            exc_type: Exception type if an exception occurred.
            exc: Exception instance if an exception occurred.
            tb: Traceback if an exception occurred.
        """
        await self.backend.__aexit__(exc_type, exc, tb)

    async def enqueue(
        self, func, *args, eta: Optional[datetime] = None, **kwargs
    ) -> str:
        """Enqueue a task for execution.

        Args:
            func: The function to execute.
            *args: Positional arguments for the function.
            eta: Optional UTC datetime for delayed execution.
            **kwargs: Keyword arguments for the function.

        Returns:
            Task ID.

        Raises:
            ValidationError: If func is not callable or eta is invalid.
            TaskQueueError: If task enqueue fails.
            SerializationError: If task serialization fails.
        """
        # Input validation
        validate(func, "func").is_required().is_callable().validate()

        if eta is not None:
            validate(eta, "eta").is_timezone_aware().validate()

        # Create task envelope using standardized serialization
        try:
            serialized_envelope = self.serializer.serialize_task_envelope(
                func, args, kwargs
            )
        except Exception as e:
            raise SerializationError(
                "Failed to serialize task envelope",
                operation="serialize",
                data_type="task_envelope",
                cause=e,
            ) from e

        # Determine available_at timestamp
        available_at = eta if eta else _now()

        # Create task
        task = Task(func=serialized_envelope, available_at=available_at)

        # Persist task
        try:
            await self.backend.enqueue(task)
        except Exception as e:
            raise TaskQueueError(
                "Failed to enqueue task in backend",
                task_id=task.id,
                operation="enqueue",
                cause=e,
            ) from e

        return task.id

    async def get_result(
        self, task_id: str, timeout: Optional[int] = None
    ) -> Optional[Result]:
        """Get the result of a task.

        Args:
            task_id: The ID of the task.
            timeout: Optional timeout in seconds.

        Returns:
            Task result or None if timeout.

        Raises:
            ValueError: If task_id is empty or timeout is negative.
        """
        # Input validation
        validate(task_id, "task_id").is_required().is_string().min_length(1).validate()

        if timeout is not None:
            validate(timeout, "timeout").is_non_negative().validate()

        start = _now()

        while True:
            try:
                result = await self.backend.get_result(task_id)
                if result:
                    return result

                if timeout and (_now() - start).total_seconds() > timeout:
                    raise TimeoutError(
                        f"Task result retrieval timed out after {timeout} seconds",
                        task_id=task_id,
                        timeout_seconds=timeout,
                        operation="get_result",
                    )

                await asyncio.sleep(0.5)
            except Exception as e:
                raise TaskQueueError(
                    f"Failed to get result for task {task_id}",
                    task_id=task_id,
                    operation="get_result",
                    cause=e,
                ) from e

    def deserialize_result(self, result: Result) -> Any:
        """Deserialize the result value from a Result object.

        Args:
            result: The Result object containing serialized value.

        Returns:
            The deserialized result value, or None if result.value is None.

        Raises:
            ValidationError: If result is None.
            SerializationError: If result deserialization fails.

        Example:
            >>> queue = TaskQueue(backend)
            >>> result = await queue.get_result(task_id)
            >>> if result and result.status == "success":
            ...     value = queue.deserialize_result(result)
        """
        validate(result, "result").is_required().validate()

        if result.value is None:
            return None

        try:
            return self.serializer.deserialize_result(result.value)
        except Exception as e:
            raise SerializationError(
                "Failed to deserialize result value",
                operation="deserialize",
                data_type="result",
                cause=e,
            ) from e

    async def close(self) -> None:
        """Close the task queue and clean up resources.

        This method closes the underlying backend connection and should be called
        when the task queue is no longer needed.

        Raises:
            BackendError: If backend cleanup fails.
        """
        await self.backend.close()
