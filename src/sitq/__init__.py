"""Simple Task Queue for Python.

sitq is a lightweight, async-first Python task queue library for running
background jobs in small-to-medium services and tools.

Key features:
- Async-first API with sync wrapper support
- SQLite backend for simple, file-based persistence
- Pluggable serialization using cloudpickle
- Comprehensive error handling and validation
- Worker support with bounded concurrency

Basic usage:
    import asyncio
    from sitq import TaskQueue, Worker, SQLiteBackend

    async def main():
        # Set up queue and worker
        backend = SQLiteBackend("tasks.db")
        queue = TaskQueue(backend=backend)
        worker = Worker(backend=backend)

        # Enqueue a task
        task_id = await queue.enqueue(lambda: "Hello, World!")

        # Start worker to process tasks
        await worker.start()
        await asyncio.sleep(1)  # Let worker process
        await worker.stop()

        # Get result
        result = await queue.get_result(task_id)
        print(result.value)  # "Hello, World!"
"""

from __future__ import annotations

# Core components
from .queue import TaskQueue
from .worker import Worker
from .sync import SyncTaskQueue
from .core import Task, Result, ReservedTask

# Backends
from .backends.base import Backend
from .backends.sqlite import SQLiteBackend

# Serialization
from .serialization import Serializer, CloudpickleSerializer

# Exceptions
from .exceptions import (
    SitqError,
    TaskQueueError,
    BackendError,
    WorkerError,
    ValidationError,
    SerializationError,
    ConnectionError,
    TaskExecutionError,
    TimeoutError,
    ResourceExhaustionError,
    ConfigurationError,
)

# Validation utilities
from .validation import validate, ValidationBuilder

__version__ = "0.1.0"
__all__ = [
    # Core components
    "TaskQueue",
    "Worker",
    "SyncTaskQueue",
    "Task",
    "Result",
    "ReservedTask",
    # Backends
    "Backend",
    "SQLiteBackend",
    # Serialization
    "Serializer",
    "CloudpickleSerializer",
    # Exceptions
    "SitqError",
    "TaskQueueError",
    "BackendError",
    "WorkerError",
    "ValidationError",
    "SerializationError",
    "ConnectionError",
    "TaskExecutionError",
    "TimeoutError",
    "ResourceExhaustionError",
    "ConfigurationError",
    # Utilities
    "validate",
    "ValidationBuilder",
]
