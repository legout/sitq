"""Synchronous task queue wrapper for sitq."""

from __future__ import annotations

import asyncio
import threading
from datetime import datetime
from typing import Optional

from .queue import TaskQueue
from .serialization import Serializer, CloudpickleSerializer
from .backends.base import Backend
from .exceptions import (
    SyncTaskQueueError,
    ValidationError,
    SerializationError,
    TaskExecutionError,
)
from .validation import (
    validate,
    validate_callable,
    validate_non_empty_string,
    validate_non_negative_number,
)


class SyncTaskQueue:
    """Synchronous wrapper for TaskQueue that manages its own event loop.

    This wrapper provides a blocking interface over the async TaskQueue,
    allowing use in synchronous code without an existing event loop.

    Note:
        Use this class only in synchronous contexts (scripts, main functions).
        In async contexts (FastAPI, async handlers), use TaskQueue directly.

    Example:
        with SyncTaskQueue(backend) as queue:
            task_id = queue.enqueue(my_function, arg1, arg2)
            result = queue.get_result(task_id, timeout=30)

    Args:
        backend: Backend instance for task persistence.
        serializer: Optional serializer instance. Defaults to CloudpickleSerializer.
    """

    def __init__(
        self,
        backend: Backend,
        serializer: Optional[Serializer] = None,
    ):
        """Initialize sync task queue wrapper.

        Args:
            backend: Backend instance for persistence.
            serializer: Optional serializer instance. Defaults to CloudpickleSerializer.

        Raises:
            ValidationError: If backend is None or invalid.
        """
        # Input validation
        validate(backend, "backend").is_required().validate()

        if serializer is not None:
            validate(serializer, "serializer").is_callable().validate()

        self.backend = backend
        self.serializer = serializer or CloudpickleSerializer()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._task_queue: Optional[TaskQueue] = None
        self._started = False

    def __enter__(self) -> "SyncTaskQueue":
        """Enter context manager and start event loop."""
        if self._started:
            raise RuntimeError(
                "SyncTaskQueue is already running - stop the current instance before creating a new one"
            )

        # Check if we're already in an event loop
        try:
            asyncio.get_running_loop()
            raise RuntimeError(
                "SyncTaskQueue cannot be used inside an existing event loop. "
                "Use TaskQueue directly in async contexts."
            )
        except RuntimeError:
            # No running loop, which is what we want
            pass

        # Create and start event loop in a separate thread
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop, name="SyncTaskQueue-EventLoop", daemon=True
        )
        self._thread.start()

        # Wait for loop to be ready
        while self._loop and not self._loop.is_running():
            import time

            time.sleep(0.001)

        # Create TaskQueue instance in the new loop
        self._task_queue = TaskQueue(self.backend, self.serializer)

        # Connect backend in the event loop thread
        if self._loop and self._task_queue:
            future = asyncio.run_coroutine_threadsafe(
                self._task_queue.__aenter__(), self._loop
            )
            future.result(timeout=5.0)  # Add timeout to prevent hanging

        self._started = True
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Exit context manager and clean up event loop."""
        if not self._started:
            return

        # Close TaskQueue and backend
        if self._task_queue and self._loop:
            asyncio.run_coroutine_threadsafe(
                self._task_queue.__aexit__(exc_type, exc, tb), self._loop
            ).result()

        # Stop the event loop
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)

        self._started = False

    def enqueue(self, func, *args, eta: Optional[datetime] = None, **kwargs) -> str:
        """Enqueue a task for execution (blocking).

        Args:
            func: The function to execute.
            *args: Positional arguments for function.
            eta: Optional UTC datetime for delayed execution.
            **kwargs: Keyword arguments for function.

        Returns:
            Task ID.

        Raises:
            RuntimeError: If SyncTaskQueue is not started.
            ValueError: If func is not callable or eta is not timezone-aware.
        """
        if not self._started or not self._task_queue or not self._loop:
            raise RuntimeError("SyncTaskQueue is not running. Use as context manager.")

        # Input validation
        validate(func, "func").is_required().is_callable().validate()

        if eta is not None:
            validate(eta, "eta").is_timezone_aware().validate()

        # Run the async enqueue in the event loop thread
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._task_queue.enqueue(func, *args, eta=eta, **kwargs), self._loop
            )
            return future.result()
        except Exception as e:
            raise SyncTaskQueueError(
                "Failed to enqueue task", operation="enqueue", cause=e
            ) from e

    def get_result(
        self, task_id: str, timeout: Optional[int] = None
    ) -> Optional[object]:
        """Get result of a task (blocking).

        Args:
            task_id: The ID of the task.
            timeout: Optional timeout in seconds.

        Returns:
            Task result or None if timeout.

        Raises:
            RuntimeError: If SyncTaskQueue is not started.
            ValueError: If task_id is empty or timeout is negative.
        """
        if not self._started or not self._task_queue or not self._loop:
            raise RuntimeError(
                "SyncTaskQueue is not running - use 'with SyncTaskQueue(...)' context manager to start it"
            )

        # Input validation
        validate(task_id, "task_id").is_required().is_string().min_length(1).validate()

        if timeout is not None:
            validate(timeout, "timeout").is_non_negative().validate()

        # Run the async get_result in the event loop thread
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._task_queue.get_result(task_id, timeout=timeout), self._loop
            )
            result = future.result()
        except Exception as e:
            raise RuntimeError(f"Failed to get result for task {task_id}: {e}") from e

        # Handle result based on status
        if result is None:
            return None

        if result.status == "failed":
            # Raise exception for failed tasks
            raise TaskExecutionError(
                f"Task {task_id} failed: {result.error}",
                task_id=task_id,
                cause=RuntimeError(result.error),
            )

        if result.status == "success" and result.value:
            # Deserialize successful result
            try:
                return self.serializer.deserialize_result(result.value)
            except Exception as e:
                raise SerializationError(
                    f"Failed to deserialize result for task {task_id}: {e}",
                    operation="deserialize",
                    data_type="result",
                    cause=e,
                ) from e

        return result

    def _run_loop(self) -> None:
        """Run the event loop in the dedicated thread."""
        if self._loop:
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

    def close(self) -> None:
        """Close the sync task queue and clean up resources."""
        if self._started:
            self.__exit__(None, None, None)
