"""Task queue implementation for sitq."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional, Union

from .serialization import Serializer, CloudpickleSerializer
from .core import Task, Result, _now
from .backends.base import Backend


class TaskQueue:
    """Async task queue for enqueuing tasks and retrieving results."""

    def __init__(
        self,
        backend: Backend,
        serializer: Optional[Serializer] = None,
    ):
        """Initialize the task queue.

        Args:
            backend: Backend instance for persistence.
            serializer: Optional serializer instance. Defaults to CloudpickleSerializer.
        """
        self.backend = backend
        self.serializer = serializer or CloudpickleSerializer()

    async def __aenter__(self):
        await self.backend.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
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
        """
        # Create task envelope as specified in serialization-core requirements
        envelope = {"func": func, "args": args, "kwargs": kwargs}

        # Determine available_at timestamp
        available_at = eta if eta else _now()

        # Create task
        task = Task(func=self.serializer.dumps(envelope), available_at=available_at)

        # Persist task
        await self.backend.enqueue(task)
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
        """
        start = _now()

        while True:
            result = await self.backend.get_result(task_id)
            if result:
                return result

            if timeout and (_now() - start).total_seconds() > timeout:
                return None

            await asyncio.sleep(0.5)

    async def close(self) -> None:
        """Close the task queue and clean up resources."""
        await self.backend.close()
