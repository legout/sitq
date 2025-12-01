"""Worker implementation for sitq."""

from __future__ import annotations

__all__ = ["Worker"]

import asyncio
import traceback
from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from .backends.base import Backend
from .core import ReservedTask
from .serialization import Serializer, CloudpickleSerializer
from .exceptions import (
    WorkerError,
    ValidationError,
    SerializationError,
    TaskExecutionError,
)
from .validation import validate, validate_callable, validate_positive_number


class Worker:
    """Worker for executing tasks from the queue."""

    def __init__(
        self,
        backend: Backend,
        serializer: Optional[Serializer] = None,
        max_concurrency: int = 1,
        poll_interval: float = 1.0,
    ):
        """Initialize the worker.

        Args:
            backend: Backend instance for task reservation and result storage.
            serializer: Optional serializer instance. Defaults to CloudpickleSerializer.
            max_concurrency: Maximum number of tasks to execute concurrently.
            poll_interval: Seconds to wait between polling attempts when no tasks available.

        Raises:
            ValueError: If max_concurrency is less than 1 or poll_interval is not positive.
        """
        # Input validation
        validate(backend, "backend").is_required().validate()

        validate(max_concurrency, "max_concurrency").is_required().in_range(
            1, 1000
        ).validate()

        validate(
            poll_interval, "poll_interval"
        ).is_required().is_positive_number().validate()

        if serializer is not None:
            validate(serializer, "serializer").is_callable().validate()

        self.backend = backend
        self.serializer = serializer or CloudpickleSerializer()
        self.max_concurrency = max_concurrency
        self.poll_interval = poll_interval

        # Runtime state
        self._running = False
        self._shutdown_event = asyncio.Event()
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._tasks: set[asyncio.Task] = set()

async def start(self) -> None:
        """Start the worker and begin processing tasks.

        This method starts the worker's polling loop, which will continuously
        check for available tasks and execute them up to the configured
        concurrency limit.

        Raises:
            BackendError: If backend connection fails.
            WorkerError: If polling loop encounters unrecoverable error.

        Example:
            >>> worker = Worker(backend, max_concurrency=5)
            >>> await worker.start()  # Runs until stop() is called
        """
        if self._running:
            logger.warning("Worker is already running")
            return

        logger.info(
            "Starting worker with max_concurrency=%d, poll_interval=%.1fs",
            self.max_concurrency,
            self.poll_interval,
        )

        self._running = True
        self._shutdown_event.clear()

        # Connect to backend if needed
        await self.backend.connect()

        try:
            await self._polling_loop()
        except Exception as e:
            logger.error("Worker polling loop failed: %s", e, exc_info=True)
            raise
        finally:
            self._running = False
            logger.info("Worker stopped")

async def stop(self) -> None:
        """Stop the worker gracefully.

        This method stops the polling loop and waits for all in-flight
        tasks to complete before returning. It will block until all
        currently executing tasks finish.

        Example:
            >>> worker = Worker(backend)
            >>> await worker.start()
            >>> await worker.stop()  # Waits for tasks to finish
        """
        if not self._running:
            logger.debug("Worker is not running")
            return

        logger.info("Stopping worker...")
        self._shutdown_event.set()

        # Wait for all in-flight tasks to complete
        if self._tasks:
            logger.info("Waiting for %d in-flight tasks to complete", len(self._tasks))
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # Close backend connection
        await self.backend.close()
        logger.info("Worker stopped gracefully")

    async def _polling_loop(self) -> None:
        """Main polling loop for reserving and executing tasks."""
        while not self._shutdown_event.is_set():
            try:
                # Reserve tasks from backend
                now = datetime.now(timezone.utc)
                reserved_tasks = await self.backend.reserve(
                    max_items=self.max_concurrency, now=now
                )

                if reserved_tasks:
                    logger.debug("Reserved %d tasks for execution", len(reserved_tasks))

                    # Execute each reserved task
                    for reserved_task in reserved_tasks:
                        task_coro = self._execute_task(reserved_task)
                        wrapped_task = self._track_task(task_coro)

                        # Start task execution with semaphore limiting
                        asyncio.create_task(self._execute_with_semaphore(wrapped_task))
                else:
                    # No tasks available, wait for poll interval
                    logger.debug(
                        "No tasks available, waiting %.1fs", self.poll_interval
                    )
                    await asyncio.sleep(self.poll_interval)

            except Exception as e:
                logger.error("Error in polling loop: %s", e, exc_info=True)
                # Wait a bit before retrying
                await asyncio.sleep(min(self.poll_interval, 1.0))

    async def _execute_with_semaphore(self, task_coro: asyncio.Task) -> None:
        """Execute task with semaphore limiting."""
        async with self._semaphore:
            if self._shutdown_event.is_set():
                logger.debug("Shutdown detected, skipping task execution")
                return
            await task_coro

    async def _execute_task(self, reserved_task: ReservedTask) -> None:
        """Execute a single reserved task."""
        task_id = reserved_task.task_id
        logger.info("Starting execution of task %s", task_id)

        try:
            # Validate reserved task
            validate(reserved_task, "reserved_task").is_required().validate()
            validate(
                reserved_task.task_id, "task_id"
            ).is_required().is_string().min_length(1).validate()

            # Deserialize and validate the task envelope
            try:
                envelope = self.serializer.deserialize_task_envelope(reserved_task.func)
            except Exception as e:
                raise SerializationError(
                    "Invalid task envelope format",
                    operation="deserialize",
                    data_type="task_envelope",
                    cause=e,
                ) from e

            func = envelope["func"]
            args = envelope["args"]
            kwargs = envelope["kwargs"]

            # Validate function is callable
            if not callable(func):
                raise ValidationError(
                    "Task envelope 'func' must be callable",
                    parameter="func",
                    value=func,
                )

            # Execute the function (async or sync)
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, lambda: func(*args, **kwargs))

            # Serialize and record success
            try:
                serialized_result = self.serializer.serialize_result(result)
                await self.backend.mark_success(task_id, serialized_result)
                logger.info("Task %s completed successfully", task_id)
            except Exception as e:
                raise WorkerError(
                    "Failed to serialize and record task success",
                    task_id=task_id,
                    operation="mark_success",
                    cause=e,
                ) from e

        except Exception as e:
            # Capture error and traceback
            error_msg = str(e)
            tb = traceback.format_exc()
            function_name = (
                getattr(func, "__name__", "unknown_function")
                if "func" in locals()
                else "unknown_function"
            )

            # Record failure
            try:
                await self.backend.mark_failure(task_id, error_msg, tb)
            except Exception as backend_error:
                logger.error(
                    "Failed to record task failure: %s", backend_error, exc_info=True
                )

            # Raise domain-specific exception
            if isinstance(e, (ValidationError, SerializationError)):
                raise TaskExecutionError(
                    f"Task execution failed: {error_msg}",
                    task_id=task_id,
                    function_name=function_name,
                    cause=e,
                ) from e
            else:
                raise TaskExecutionError(
                    f"Task execution failed: {error_msg}",
                    task_id=task_id,
                    function_name=function_name,
                    cause=e,
                ) from e

            logger.error("Task %s failed: %s", task_id, error_msg, exc_info=True)

    def _track_task(self, coro) -> asyncio.Task:
        """Track a task and remove it from the set when done."""
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task
