"""Worker implementation for sitq."""

from __future__ import annotations

from typing import Optional
from .serialization import Serializer, CloudpickleSerializer


class Worker:
    """Worker for executing tasks from the queue."""

    def __init__(
        self,
        serializer: Optional[Serializer] = None,
    ):
        """Initialize the worker.

        Args:
            serializer: Optional serializer instance. Defaults to CloudpickleSerializer.
        """
        self.serializer = serializer or CloudpickleSerializer()

    async def start(self) -> None:
        """Start the worker."""
        # TODO: Implement start logic
        raise NotImplementedError("Worker.start not yet implemented")

    async def stop(self) -> None:
        """Stop the worker."""
        # TODO: Implement stop logic
        raise NotImplementedError("Worker.stop not yet implemented")
