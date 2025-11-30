"""
Async Worker implementation for executing tasks from the backend.
"""

import asyncio
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Optional, Set
from loguru import logger

# Import our modules directly from relative paths to avoid queue.py conflict
from .backends.base import Backend, ReservedTask
from .serialization import Serializer, CloudpickleSerializer


class Worker:
    """
    Async worker for executing tasks from the backend.

    The worker polls the backend for executable tasks, executes them with
    bounded concurrency, and records the results using the backend.

    Args:
        backend: Backend implementation for task persistence
        serializer: Serializer for task payloads and results.
                   Defaults to CloudpickleSerializer.
        concurrency: Maximum number of concurrent tasks. Defaults to 1.
        poll_interval: Time between polls when no tasks are available. Defaults to 1.0 seconds.
        custom_logger: Logger instance. If None, uses loguru's default logger.
    """

    def __init__(
        self,
        backend: Backend,
        serializer: Optional[Serializer] = None,
        max_concurrency: int = 1,
        poll_interval: float = 1.0,
        batch_size: int = 1,
        custom_logger: Optional[Any] = None,
    ):
        self.backend = backend
        self.serializer = serializer or CloudpickleSerializer()
        self.max_concurrency = max_concurrency
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        self.logger = custom_logger or logger

        self._running = False
        self._task = None
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._executor = ThreadPoolExecutor(max_workers=max_concurrency)
        self._running_tasks: Set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """
        Start the worker and begin processing tasks.
        """
        if self._running:
            self.logger.info("Worker is already running")
            return

        self._running = True
        self._shutdown_event.clear()
        self._task = asyncio.create_task(self._run())
        self.logger.info(
            f"Worker started with max_concurrency={self.max_concurrency}, poll_interval={self.poll_interval}s, batch_size={self.batch_size}"
        )

    async def stop(self) -> None:
        """
        Stop the worker and wait for in-flight tasks to complete.
        """
        if not self._running:
            self.logger.info("Worker is not running")
            return

        self.logger.info("Stopping worker...")
        self._running = False
        self._shutdown_event.set()

        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=30.0)
            except asyncio.TimeoutError:
                self.logger.warning(
                    "Worker did not stop within timeout, cancelling remaining tasks"
                )
                # Cancel any remaining running tasks and reset their status
                await self._cancel_and_reset_running_tasks()

        # Always reset any tasks that might still be in progress
        await self._cancel_and_reset_running_tasks()

        # Clean up executor
        self._executor.shutdown(wait=True)
        self.logger.info("Worker stopped")

    async def _cancel_and_reset_running_tasks(self) -> None:
        """
        Cancel all running tasks and reset their status to pending.
        This ensures tasks can be retried by other workers.
        """
        for task in list(self._running_tasks):
            if not task.done():
                task.cancel()

        # Wait for all tasks to be cancelled
        if self._running_tasks:
            await asyncio.gather(*self._running_tasks, return_exceptions=True)

        # Reset any tasks that were still in progress back to pending
        try:
            conn = await self.backend._get_connection()
            conn.execute("""
                UPDATE tasks 
                SET status = 'pending', started_at = NULL
                WHERE status = 'in_progress'
            """)
            conn.commit()
            self.logger.info(
                f"Reset {len(self._running_tasks)} tasks back to pending state"
            )
        except Exception as e:
            self.logger.error(f"Failed to reset task statuses: {e}")

    async def _run(self) -> None:
        """
        Main worker loop that polls for and executes tasks.
        """
        self.logger.info("Worker polling loop started")

        try:
            while self._running:
                # Calculate how many tasks we can reserve:
                # - Limited by batch_size (don't reserve too many at once)
                # - Limited by max_concurrency minus currently running tasks
                running_count = len(self._running_tasks)
                available_slots = max(0, self.max_concurrency - running_count)
                max_to_reserve = min(self.batch_size, available_slots)

                # Try to reserve and execute tasks
                if max_to_reserve > 0:
                    reserved_tasks = await self.backend.reserve(
                        max_items=max_to_reserve, now=datetime.now(timezone.utc)
                    )
                else:
                    reserved_tasks = []

                if reserved_tasks:
                    self.logger.debug(f"Reserved {len(reserved_tasks)} tasks")

                    # Execute each reserved task with concurrency control
                    for reserved_task in reserved_tasks:
                        # Use semaphore to limit concurrency
                        async with self._semaphore:
                            if self._running:  # Check we're still running
                                task = asyncio.create_task(
                                    self._execute_task(reserved_task)
                                )
                                self._running_tasks.add(task)
                                task.add_done_callback(self._running_tasks.discard)

                if not reserved_tasks and self._running:
                    # No tasks available, wait for poll interval or shutdown
                    try:
                        await asyncio.wait_for(
                            self._shutdown_event.wait(), timeout=self.poll_interval
                        )
                        # Shutdown event was set, break out of loop
                        break
                    except asyncio.TimeoutError:
                        # Continue polling
                        pass

        except Exception as e:
            self.logger.error(f"Worker loop error: {e}")
            self.logger.error(traceback.format_exc())
        finally:
            self.logger.info("Worker polling loop ended")

    async def _execute_task(self, reserved_task: ReservedTask) -> None:
        """
        Execute a reserved task using the serializer and backend.

        Args:
            reserved_task: Task reserved from the backend
        """
        task_id = reserved_task.task_id
        payload_data = reserved_task.payload

        self.logger.info(f"Starting task {task_id[:8]}...")
        start_time = datetime.now(timezone.utc)

        try:
            # Deserialize task payload
            payload = self.serializer.loads(payload_data)

            if not isinstance(payload, dict) or "func" not in payload:
                raise ValueError(f"Invalid task payload format for task {task_id}")

            func = payload["func"]
            args = payload.get("args", ())
            kwargs = payload.get("kwargs", {})

            # Check if callable is async or sync
            if asyncio.iscoroutinefunction(func):
                self.logger.debug(f"Executing async task {task_id[:8]}...")
                result_value = await func(*args, **kwargs)
            else:
                self.logger.debug(f"Executing sync task {task_id[:8]}...")
                loop = asyncio.get_event_loop()
                result_value = await loop.run_in_executor(
                    self._executor, lambda: func(*args, **kwargs)
                )

            # Mark task as successful
            await self.backend.mark_success(
                task_id, result_value, datetime.now(timezone.utc)
            )

            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.logger.info(
                f"Task {task_id[:8]} completed successfully in {execution_time:.2f}s"
            )

        except Exception as e:
            # Mark task as failed
            error_msg = str(e)
            tb = traceback.format_exc()

            await self.backend.mark_failure(
                task_id, error_msg, tb, datetime.now(timezone.utc)
            )

            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.logger.error(
                f"Task {task_id[:8]} failed after {execution_time:.2f}s: {error_msg}"
            )

    async def __aenter__(self) -> "Worker":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()
