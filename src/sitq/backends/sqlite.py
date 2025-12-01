"""SQLite backend implementation for sitq."""

import json
import asyncio
import uuid
import aiosqlite
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator, List, Optional, Sequence

from ..core import Result, ReservedTask, Task

__all__ = ["SQLiteBackend"]
from ..exceptions import BackendError, ValidationError, ConnectionError
from ..validation import validate, validate_optional, retry_async
from .base import Backend


class SQLiteBackend(Backend):
    """SQLite backend for task queue persistence.

    This backend provides persistent storage using SQLite database files or
    in-memory databases for testing and development. It supports
    concurrent access through WAL mode and proper connection management.

    Attributes:
        database_path: Path to SQLite database file or ":memory:" for in-memory.
        _initialized: Whether database schema has been initialized.
        _is_memory: Whether using in-memory database.
        _shared_connection: Shared connection for in-memory databases.
        _connection_lock: Lock for thread-safe connection access.

    Example:
        >>> backend = SQLiteBackend("tasks.db")
        >>> await backend.connect()
        >>> # Use backend for task operations
    """

    def __init__(self, database_path: str = ":memory:"):
        """Initialize SQLite backend.

        Args:
            database_path: Path to SQLite database file. Use ":memory:" for
                in-memory database (useful for testing).

        Raises:
            ValidationError: If database_path is not a valid string.

        Example:
            >>> backend = SQLiteBackend("tasks.db")  # File database
            >>> backend = SQLiteBackend(":memory:")  # In-memory database
        """
        # Validate database_path parameter
        validate(database_path, "database_path").is_required().is_string()

        self.database_path = database_path
        self._initialized = False
        self._is_memory = database_path == ":memory:"
        self._shared_connection = None
        self._connection_lock = asyncio.Lock()

    @retry_async(max_attempts=3, base_delay=0.5, max_delay=5.0)
    async def _get_connection(self) -> aiosqlite.Connection:
        """Get a database connection, shared for in-memory databases."""
        try:
            if self._is_memory:
                async with self._connection_lock:
                    if self._shared_connection is None:
                        self._shared_connection = await aiosqlite.connect(
                            self.database_path
                        )
                    return self._shared_connection
            else:
                # For file databases, create new connection each time
                return await aiosqlite.connect(self.database_path)
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to SQLite database '{self.database_path}': {e}",
                backend_type="sqlite",
                connection_details=f"database_path={self.database_path}",
                cause=e,
            ) from e

    async def _with_connection(self, operation_func):
        """Execute an operation with proper connection handling."""
        if self._is_memory:
            db = await self._get_connection()
            return await operation_func(db)
        else:
            async with await self._get_connection() as db:
                return await operation_func(db)

    async def initialize(self) -> None:
        """Initialize database schema and apply migrations."""
        if self._initialized:
            return

        async def init_db(db):
            # Configure SQLite for better concurrency
            await db.execute(
                "PRAGMA journal_mode=WAL"
            )  # Enable WAL mode for multi-process safety
            await db.execute(
                "PRAGMA synchronous=NORMAL"
            )  # Balance between safety and performance
            await db.execute(
                "PRAGMA cache_size=10000"
            )  # Increase cache size for better performance
            await db.execute(
                "PRAGMA temp_store=MEMORY"
            )  # Store temporary tables in memory
            await db.execute(
                "PRAGMA mmap_size=268435456"
            )  # Enable memory-mapped I/O (256MB)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    func BLOB NOT NULL,
                    args BLOB,
                    kwargs BLOB,
                    context BLOB,
                    schedule TEXT,
                    created_at TIMESTAMP NOT NULL,
                    available_at TIMESTAMP NOT NULL,
                    last_run_time TIMESTAMP,
                    result_id TEXT,
                    retries INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    retry_backoff INTEGER DEFAULT 1,
                    lock_id TEXT,
                    locked_until TIMESTAMP,
                    status TEXT NOT NULL DEFAULT 'pending',
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    result_data BLOB,
                    error_message TEXT,
                    traceback TEXT
                )
            """)

            # Create indexes for performance
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status_available 
                ON tasks(status, available_at, created_at)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status 
                ON tasks(status)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_lock_id 
                ON tasks(lock_id)
            """)

            await db.commit()

        await self._with_connection(init_db)
        self._initialized = True

    @retry_async(max_attempts=3, base_delay=0.5, max_delay=5.0)
    async def enqueue(self, task: Task) -> None:
        """Add a task to the queue."""
        # Validate task parameter
        if task is None:
            raise ValidationError(
                "Task cannot be None - provide a valid Task instance", parameter="task"
            )

        await self.initialize()

        async def enqueue_task(db):
            await db.execute(
                """
                INSERT INTO tasks (
                    task_id, func, args, kwargs, context, schedule,
                    created_at, available_at, last_run_time, result_id,
                    retries, max_retries, retry_backoff, lock_id, locked_until,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    task.id,
                    task.func,  # Store serialized function as bytes
                    task.args,
                    task.kwargs,
                    task.context,
                    None,  # schedule
                    task.created_at.isoformat(),
                    task.available_at.isoformat(),
                    None,  # last_run_time
                    None,  # result_id
                    task.retries,
                    task.max_retries,
                    1,  # retry_backoff
                    None,  # lock_id
                    None,  # locked_until
                    "pending",
                ),
            )
            await db.commit()

        try:
            await self._with_connection(enqueue_task)
        except Exception as e:
            raise BackendError(
                f"Failed to enqueue task {task.id}: {e}",
                operation="enqueue",
                task_id=task.id,
                backend_type="sqlite",
                cause=e,
            ) from e

    @retry_async(max_attempts=3, base_delay=0.5, max_delay=5.0)
    async def reserve(self, max_items: int, now: datetime) -> List[ReservedTask]:
        """Reserve tasks for execution."""
        # Validate parameters
        validate(max_items, "max_items").is_required().is_integer().is_positive_number()
        validate(now, "now").is_required().is_timezone_aware()

        await self.initialize()

        async def reserve_tasks(db):
            now_iso = now.isoformat()

            # Use transaction to atomically reserve tasks
            async with db.execute(
                """
                UPDATE tasks 
                SET status = 'reserved', started_at = ?, lock_id = ?, locked_until = ?
                WHERE task_id IN (
                    SELECT task_id FROM tasks
                    WHERE status = 'pending'
                    AND available_at <= ?
                    ORDER BY available_at, created_at
                    LIMIT ?
                )
                RETURNING task_id, func, context, started_at
            """,
                (now_iso, str(uuid.uuid4()), None, now_iso, max_items),
            ) as cursor:
                rows = await cursor.fetchall()

            reserved_tasks = []
            for row in rows:
                task_id, func, context, started_at = row

                reserved_tasks.append(
                    ReservedTask(
                        task_id=task_id,
                        func=func,
                        context=context,
                        started_at=datetime.fromisoformat(started_at),
                    )
                )

            await db.commit()
            return reserved_tasks

        try:
            return await self._with_connection(reserve_tasks)
        except Exception as e:
            raise BackendError(
                f"Failed to reserve tasks: {e}",
                operation="reserve",
                backend_type="sqlite",
                cause=e,
            ) from e

    async def mark_success(self, task_id: str, result_value: bytes) -> None:
        """Mark a task as successfully completed."""
        # Validate parameters
        validate(task_id, "task_id").is_required().is_non_empty_string()
        validate(result_value, "result_value").is_required()

        await self.initialize()

        async def mark_success_task(db):
            now = datetime.now(timezone.utc).isoformat()

            await db.execute(
                """
                UPDATE tasks 
                SET status = 'completed', result_data = ?, completed_at = ?
                WHERE task_id = ?
            """,
                (result_value, now, task_id),
            )
            await db.commit()

        try:
            await self._with_connection(mark_success_task)
        except Exception as e:
            raise BackendError(
                f"Failed to mark task {task_id} as success: {e}",
                operation="mark_success",
                task_id=task_id,
                backend_type="sqlite",
                cause=e,
            ) from e

    async def mark_failure(self, task_id: str, error: str, traceback: str) -> None:
        """Mark a task as failed."""
        # Validate parameters
        validate(task_id, "task_id").is_required().is_non_empty_string()
        validate(error, "error").is_required().is_string()
        validate(traceback, "traceback").is_required().is_string()

        await self.initialize()

        async def mark_failure_task(db):
            now = datetime.now(timezone.utc).isoformat()

            await db.execute(
                """
                UPDATE tasks 
                SET status = 'failed', error_message = ?, traceback = ?, completed_at = ?
                WHERE task_id = ?
            """,
                (error, traceback, now, task_id),
            )
            await db.commit()

        try:
            await self._with_connection(mark_failure_task)
        except Exception as e:
            raise BackendError(
                f"Failed to mark task {task_id} as failed: {e}",
                operation="mark_failure",
                task_id=task_id,
                backend_type="sqlite",
                cause=e,
            ) from e

    async def get_result(self, task_id: str) -> Optional[Result]:
        """Get the result of a task."""
        # Validate task_id parameter
        validate(task_id, "task_id").is_required().is_non_empty_string()

        await self.initialize()

        async def get_result_task(db):
            async with db.execute(
                """
                SELECT status, result_data, error_message, traceback, 
                       created_at, started_at, completed_at
                FROM tasks
                WHERE task_id = ?
            """,
                (task_id,),
            ) as cursor:
                row = await cursor.fetchone()
            if row is None:
                return None

            (
                status,
                result_data,
                error_message,
                traceback,
                created_at,
                started_at,
                completed_at,
            ) = row

            if status == "completed":
                return Result(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    status="success",
                    value=result_data,  # result_data is already bytes
                    error=None,
                    traceback=None,
                    enqueued_at=datetime.fromisoformat(created_at),
                    started_at=datetime.fromisoformat(started_at)
                    if started_at
                    else None,
                    finished_at=datetime.fromisoformat(completed_at)
                    if completed_at
                    else None,
                )
            elif status == "failed":
                return Result(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    status="failed",
                    value=None,
                    error=error_message,
                    traceback=traceback,
                    enqueued_at=datetime.fromisoformat(created_at),
                    started_at=datetime.fromisoformat(started_at)
                    if started_at
                    else None,
                    finished_at=datetime.fromisoformat(completed_at)
                    if completed_at
                    else None,
                )
            else:
                # Task is still pending or reserved
                return None

        try:
            return await self._with_connection(get_result_task)
        except Exception as e:
            raise BackendError(
                f"Failed to get result for task {task_id}: {e}",
                operation="get_result",
                task_id=task_id,
                backend_type="sqlite",
                cause=e,
            ) from e

    async def get_pending_tasks(self, limit: int = 100) -> AsyncGenerator[Task, None]:
        """Get pending tasks for processing."""
        await self.initialize()

        async with await self._get_connection() as db:
            async with db.execute(
                """
                SELECT task_id, func, args, kwargs, context, schedule,
                       created_at, available_at, last_run_time, result_id,
                       retries, max_retries, retry_backoff, lock_id, locked_until
                FROM tasks
                WHERE status = 'pending'
                ORDER BY available_at, created_at
                LIMIT ?
            """,
                (limit,),
            ) as cursor:
                async for row in cursor:
                    task = self._row_to_task(row)
                    yield task

    async def get_expired_tasks(self, now: datetime) -> AsyncGenerator[Task, None]:
        """Get expired tasks."""
        await self.initialize()

        async with await self._get_connection() as db:
            now_iso = now.isoformat()
            async with db.execute(
                """
                SELECT task_id, func, args, kwargs, context, schedule,
                       created_at, available_at, last_run_time, result_id,
                       retries, max_retries, retry_backoff, lock_id, locked_until
                FROM tasks
                WHERE status = 'pending' AND locked_until IS NOT NULL AND locked_until <= ?
                ORDER BY locked_until
            """,
                (now_iso,),
            ) as cursor:
                async for row in cursor:
                    task = self._row_to_task(row)
                    yield task

    async def delete_task(self, task_id: str) -> None:
        """Delete a task from the queue."""
        await self.initialize()

        async with await self._get_connection() as db:
            await db.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
            await db.commit()

    async def get_queue_stats(self) -> dict:
        """Get queue statistics."""
        await self.initialize()

        async with await self._get_connection() as db:
            stats = {}

            for status in ["pending", "reserved", "completed", "failed"]:
                async with db.execute(
                    "SELECT COUNT(*) FROM tasks WHERE status = ?", (status,)
                ) as cursor:
                    count = await cursor.fetchone()
                    stats[status] = count[0] if count else 0

            return stats

    def _row_to_task(self, row: Sequence) -> Task:
        """Convert database row to Task object."""
        (
            task_id,
            func,
            args,
            kwargs,
            context,
            schedule,
            created_at,
            available_at,
            last_run_time,
            result_id,
            retries,
            max_retries,
            retry_backoff,
            lock_id,
            locked_until,
        ) = row

        return Task(
            id=task_id,
            func=func,  # Already serialized bytes
            args=args,
            kwargs=kwargs,
            context=context,  # Already serialized bytes
            schedule=json.loads(schedule) if schedule else None,
            created_at=datetime.fromisoformat(created_at),
            available_at=datetime.fromisoformat(available_at),
            last_run_time=datetime.fromisoformat(last_run_time)
            if last_run_time
            else None,
            result_id=result_id,
            retries=retries,
            max_retries=max_retries,
            retry_backoff=retry_backoff,
            lock_id=lock_id,
            locked_until=datetime.fromisoformat(locked_until) if locked_until else None,
        )

    # Legacy compatibility methods
    async def fetch_due_tasks(self, limit: int = 1) -> List[Task]:
        """Return up to limit tasks that are ready to run."""
        reserved_tasks = await self.reserve(limit, datetime.now(timezone.utc))
        return [
            Task(
                id=rt.task_id,
                func=rt.func,
                args=None,  # Not available in ReservedTask
                kwargs=None,  # Not available in ReservedTask
                context=rt.context,
                created_at=rt.started_at,
                available_at=rt.started_at,
                last_run_time=None,
                result_id=None,
                retries=0,
                max_retries=3,
                retry_backoff=1,
                lock_id=None,
                locked_until=None,
                schedule=None,
            )
            for rt in reserved_tasks
        ]

    async def update_task_state(self, task_id: str, **kwargs) -> None:
        """Patch a task row (e.g. available_at, retries)."""
        await self.initialize()

        if not kwargs:
            return

        # Build dynamic UPDATE query
        set_clauses = []
        values = []

        for key, value in kwargs.items():
            if key in ["retries", "max_retries", "retry_backoff"]:
                set_clauses.append(f"{key} = ?")
                values.append(value)
            elif key in ["available_at", "last_run_time", "locked_until"]:
                set_clauses.append(f"{key} = ?")
                values.append(value.isoformat() if value else None)
            elif key in ["lock_id", "result_id"]:
                set_clauses.append(f"{key} = ?")
                values.append(value)
            elif key == "schedule":
                set_clauses.append(f"{key} = ?")
                values.append(json.dumps(value) if value else None)

        if set_clauses:
            sql = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE task_id = ?"
            values.append(task_id)

            async with await self._get_connection() as db:
                await db.execute(sql, values)
            await db.commit()

    async def connect(self) -> None:
        """Open database connection and initialize schema.

        This method establishes connection to the SQLite database and ensures
        the required tables and indexes are created. For in-memory
        databases, maintains a shared connection for all operations.

        Raises:
            ConnectionError: If database connection or initialization fails.

        Example:
            >>> backend = SQLiteBackend("tasks.db")
            >>> await backend.connect()
            >>> # Backend is ready for operations
        """
        try:
            await self.initialize()
        except Exception as e:
            raise ConnectionError(
                f"Failed to initialize SQLite backend: {e}",
                backend_type="sqlite",
                connection_details=f"database_path={self.database_path}",
                cause=e,
            ) from e

async def close(self) -> None:
        """Close database connection and clean up resources.

        This method closes the database connection and cleans up any
        allocated resources. For in-memory databases, it closes the
        shared connection.

        Raises:
            ConnectionError: If database connection cleanup fails.

        Example:
            >>> backend = SQLiteBackend("tasks.db")
            >>> await backend.connect()
            >>> await backend.close()  # Clean shutdown
        """
        try:
            if self._shared_connection is not None:
                await self._shared_connection.close()
                self._shared_connection = None
        except Exception as e:
            raise ConnectionError(
                f"Failed to close SQLite database connection: {e}",
                backend_type="sqlite",
                connection_details=f"database_path={self.database_path}",
                cause=e,
            ) from e

    async def store_result(self, result: Result) -> None:
        """Persist a task result."""
        await self.initialize()

        if result.error:
            await self.mark_failure(
                result.task_id, result.error, result.traceback or ""
            )
        else:
            await self.mark_success(result.task_id, result.value or b"")

    async def claim_task(self, task_id: str, lock_timeout: int = 30) -> bool:
        """Atomically claim a task for processing."""
        await self.initialize()

        async with await self._get_connection() as db:
            now = datetime.now(timezone.utc)
            lock_id = str(uuid.uuid4())
            locked_until = now + timedelta(seconds=lock_timeout)

            # Try to update the task status to 'reserved' if it's still pending
            cursor = await db.execute(
                """
                UPDATE tasks 
                SET status = 'reserved', started_at = ?, lock_id = ?, locked_until = ?
                WHERE task_id = ? AND status = 'pending'
            """,
                (now.isoformat(), lock_id, locked_until.isoformat(), task_id),
            )

            await db.commit()
            return cursor.rowcount > 0

    async def release_task(self, task_id: str) -> None:
        """Release lock for task_id (called when a worker aborts)."""
        await self.initialize()

        async with await self._get_connection() as db:
            await db.execute(
                """
                UPDATE tasks 
                SET status = 'pending', started_at = NULL, lock_id = NULL, locked_until = NULL
                WHERE task_id = ? AND status = 'reserved'
            """,
                (task_id,),
            )
            await db.commit()

    async def schedule_retry(self, task_id: str, delay: int) -> None:
        """Reschedule a failed task after delay seconds and bump retry counter."""
        await self.initialize()

        async with await self._get_connection() as db:
            # Calculate new available_at time and increment retry count
            new_available_at = datetime.now(timezone.utc) + timedelta(seconds=delay)

            await db.execute(
                """
                UPDATE tasks 
                SET status = 'pending', 
                    available_at = ?,
                    retries = retries + 1,
                    started_at = NULL,
                    completed_at = NULL,
                    lock_id = NULL,
                    locked_until = NULL
                WHERE task_id = ?
            """,
                (new_available_at.isoformat(), task_id),
            )
            await db.commit()
