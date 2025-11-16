"""
Synchronous TaskQueue wrapper for non-async Python code.

This module provides SyncTaskQueue, a blocking wrapper around the async
TaskQueue that allows synchronous code to enqueue tasks and get results
without requiring an event loop.
"""

import asyncio
from datetime import datetime
from typing import Any, Optional

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from backends.base import Backend
from serialization import Serializer, CloudpickleSerializer
from queue import TaskQueue
from result import Result


class SyncTaskQueue:
    """
    Synchronous wrapper around the async TaskQueue for non-async Python code.

    This class provides a blocking interface that owns and manages an internal
    asyncio event loop, allowing synchronous code to use the task queue
    functionality without manual event loop management.

    Usage constraints:
    - Use in synchronous contexts only (not inside async functions)
    - Use as a context manager to ensure proper resource cleanup
    - Use the async TaskQueue directly when inside async frameworks

    Args:
        backend: Backend implementation for task persistence
        serializer: Serializer for task payloads and results.
                   Defaults to CloudpickleSerializer.

    Example:
        with SyncTaskQueue(backend) as queue:
            task_id = queue.enqueue(my_function, arg1, arg2)
            result = queue.get_result(task_id)
    """

    def __init__(self, backend: Backend, serializer: Optional[Serializer] = None):
        self.backend = backend
        self.serializer = serializer or CloudpickleSerializer()
        self._task_queue: Optional[TaskQueue] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def __enter__(self) -> "SyncTaskQueue":
        """
        Enter the context manager and create the async resources.

        Returns:
            SyncTaskQueue: self for use with 'as' clause
        """
        self._ensure_loop()
        self._task_queue = TaskQueue(self.backend, self.serializer)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context manager and cleanup async resources.
        """
        self.close()
        return False

    def _ensure_loop(self):
        """Ensure we have an event loop, create one if needed."""
        try:
            # Try to get the current running loop
            self._loop = asyncio.get_running_loop()
            if self._loop.is_running():
                raise ValueError(
                    "SyncTaskQueue cannot be used inside an existing async context. "
                    "Use the async TaskQueue directly instead."
                )
        except RuntimeError:
            # No running loop, create a new one
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

    def _run_async(self, coro):
        """
        Run an async coroutine in our event loop.

        Args:
            coro: The coroutine to run

        Returns:
            The result of the coroutine
        """
        if self._loop is None:
            raise RuntimeError(
                "SyncTaskQueue not properly initialized. Use as context manager."
            )

        if self._loop.is_running():
            raise RuntimeError(
                "SyncTaskQueue event loop is already running. "
                "This should not happen in normal usage."
            )

        return self._loop.run_until_complete(coro)

    def enqueue(
        self, func: Any, *args: Any, eta: Optional[datetime] = None, **kwargs: Any
    ) -> str:
        """
        Enqueue a task for execution (synchronous version).

        Args:
            func: Callable to execute
            *args: Positional arguments for the callable
            eta: Optional execution time. If None, task is available immediately.
            **kwargs: Keyword arguments for the callable

        Returns:
            str: Task ID for result retrieval
        """
        if self._task_queue is None:
            raise RuntimeError(
                "SyncTaskQueue not initialized. Use as context manager: "
                "'with SyncTaskQueue(backend) as queue:'"
            )

        return self._run_async(self._task_queue.enqueue(func, *args, eta=eta, **kwargs))

    def get_result(
        self, task_id: str, timeout: Optional[float] = None
    ) -> Optional[Result]:
        """
        Retrieve the result of a completed task (synchronous version).

        Args:
            task_id: ID of the task to retrieve result for
            timeout: Optional timeout in seconds

        Returns:
            Result: Result object if task completed, None if not ready or timeout
        """
        if self._task_queue is None:
            raise RuntimeError(
                "SyncTaskQueue not initialized. Use as context manager: "
                "'with SyncTaskQueue(backend) as queue:'"
            )

        return self._run_async(self._task_queue.get_result(task_id, timeout=timeout))

    def close(self):
        """
        Close the TaskQueue and cleanup resources.

        This method is called automatically when exiting the context manager,
        but can be called explicitly if needed.
        """
        if self._task_queue is not None:
            self._run_async(self._task_queue.close())
            self._task_queue = None

        if self._loop is not None and not self._loop.is_running():
            self._loop.close()
            self._loop = None
