import asyncio
import json
import sqlite3
import uuid
import aiosqlite
from datetime import datetime, timezone, timedelta
from typing import Any, AsyncGenerator, List, Optional, Tuple, Sequence

from ..core import Result, ReservedTask, Task
from .base import Backend


class SQLiteBackend(Backend):
    """SQLite backend for task queue persistence."""

    def __init__(self, database_path: str = ":memory:"):
        self.database_path = database_path
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize database schema and apply migrations."""
        if self._initialized:
            return

        async with aiosqlite.connect(self.database_path) as db:
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
                    task_data BLOB NOT NULL,
                    result_data BLOB,
                    error_message TEXT,
                    traceback TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP NOT NULL,
                    eta_at TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 0,
                    context BLOB
                )
            """)

            # Create indexes for performance
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status_eta 
                ON tasks(status, eta_at, created_at)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status 
                ON tasks(status)
            """)

            await db.commit()

        self._initialized = True

    async def connect(self) -> None:
        """Open any required connections (DB, network, etc.)."""
        await self.initialize()

    async def close(self) -> None:
        """Close / clean up all resources."""
        # SQLite connections are managed per-method, so no persistent resources to clean up
        pass

    async def enqueue(self, task: Task) -> None:
        """Add a task to the queue."""
        await self.initialize()

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(
                """
                INSERT INTO tasks (
                    task_id, task_data, status, created_at, eta_at, 
                    expires_at, retry_count, max_retries, context
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    task.id,
                    task.func,  # Store serialized function as bytes
                    "pending",
                    task.created_at.isoformat(),
                    task.available_at.isoformat()
                    if task.available_at != task.created_at
                    else None,
                    None,  # expires_at - not in current Task model
                    task.retries,
                    task.max_retries,
                    task.context,  # Store serialized context as bytes
                ),
            )
            await db.commit()

    async def reserve(self, max_items: int, now: datetime) -> List[ReservedTask]:
        """Reserve tasks for execution."""
        await self.initialize()

        async with aiosqlite.connect(self.database_path) as db:
            now_iso = now.isoformat()

            # Use transaction to atomically reserve tasks
            async with db.execute(
                """
                UPDATE tasks 
                SET status = 'reserved', started_at = ?
                WHERE task_id IN (
                    SELECT task_id FROM tasks
                    WHERE status = 'pending'
                    AND (eta_at IS NULL OR eta_at <= ?)
                    ORDER BY eta_at, created_at
                    LIMIT ?
                )
                RETURNING task_id, task_data, context, started_at
            """,
                (now_iso, now_iso, max_items),
            ) as cursor:
                rows = await cursor.fetchall()

            reserved_tasks = []
            for row in rows:
                task_id, task_data, context, started_at = row

                reserved_tasks.append(
                    ReservedTask(
                        task_id=task_id,
                        func=task_data,  # task_data is already serialized bytes
                        context=context,  # context is already serialized bytes
                        started_at=datetime.fromisoformat(started_at),
                    )
                )

            await db.commit()
            return reserved_tasks

    async def mark_success(self, task_id: str, result_value: bytes) -> None:
        """Mark a task as successfully completed."""
        await self.initialize()

        async with aiosqlite.connect(self.database_path) as db:
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

    async def mark_failure(self, task_id: str, error: str, traceback: str) -> None:
        """Mark a task as failed."""
        await self.initialize()

        async with aiosqlite.connect(self.database_path) as db:
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

    async def get_result(self, task_id: str) -> Optional[Result]:
        """Get the result of a task."""
        await self.initialize()

        async with aiosqlite.connect(self.database_path) as db:
            async with db.execute(
                """
                SELECT status, result_data, error_message, traceback, created_at, completed_at
                FROM tasks
                WHERE task_id = ?
            """,
                (task_id,),
            ) as cursor:
                row = await cursor.fetchone()

            if row is None:
                return None

            status, result_data, error_message, traceback, created_at, completed_at = (
                row
            )

            if status == "completed":
                return Result(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    status="success",
                    value=result_data,  # result_data is already bytes
                    error=None,
                    traceback=None,
                    enqueued_at=datetime.fromisoformat(created_at),
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
                    finished_at=datetime.fromisoformat(completed_at)
                    if completed_at
                    else None,
                )
            else:
                # Task is still pending or reserved
                return None

            status, result_data, error_message, traceback, created_at, completed_at = (
                row
            )

            if status == "completed":
                result_dict = json.loads(result_data) if result_data else {}
                return Result(
                    value=result_dict.get("value"),
                    error=None,
                    traceback=None,
                    created_at=datetime.fromisoformat(created_at),
                    completed_at=datetime.fromisoformat(completed_at)
                    if completed_at
                    else None,
                )
            elif status == "failed":
                return Result(
                    value=None,
                    error=error_message,
                    traceback=traceback,
                    created_at=datetime.fromisoformat(created_at),
                    completed_at=datetime.fromisoformat(completed_at)
                    if completed_at
                    else None,
                )
            else:
                # Task is still pending or reserved
                return None

    async def get_pending_tasks(self, limit: int = 100) -> AsyncGenerator[Task, None]:
        """Get pending tasks for processing."""
        await self.initialize()

        async with aiosqlite.connect(self.database_path) as db:
            async with db.execute(
                """
                SELECT task_id, task_data, created_at, eta_at, expires_at, 
                       retry_count, max_retries, context
                FROM tasks
                WHERE status = 'pending'
                ORDER BY eta_at, created_at
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

        async with aiosqlite.connect(self.database_path) as db:
            now_iso = now.isoformat()
            async with db.execute(
                """
                SELECT task_id, task_data, created_at, eta_at, expires_at,
                       retry_count, max_retries, context
                FROM tasks
                WHERE status = 'pending' AND expires_at IS NOT NULL AND expires_at <= ?
                ORDER BY expires_at
            """,
                (now_iso,),
            ) as cursor:
                async for row in cursor:
                    task = self._row_to_task(row)
                    yield task

    async def delete_task(self, task_id: str) -> None:
        """Delete a task from the queue."""
        await self.initialize()

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
            await db.commit()

    async def get_queue_stats(self) -> dict:
        """Get queue statistics."""
        await self.initialize()

        async with aiosqlite.connect(self.database_path) as db:
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
            task_data,
            created_at,
            eta_at,
            expires_at,
            retry_count,
            max_retries,
            context,
        ) = row

        task_dict = json.loads(task_data)
        context_dict = json.loads(context) if context else {}

        return Task(
            task_id=task_id,
            func=task_dict["func"],
            args=task_dict["args"],
            kwargs=task_dict["kwargs"],
            created_at=datetime.fromisoformat(created_at),
            eta_at=datetime.fromisoformat(eta_at) if eta_at else None,
            expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
            retry_count=retry_count,
            max_retries=max_retries,
            context=context_dict,
        )

    # Legacy compatibility methods
    async def fetch_due_tasks(self, limit: int = 1) -> List[Task]:
        """Return up to limit tasks that are ready to run."""
        reserved_tasks = await self.reserve(limit, datetime.now(timezone.utc))
        return [
            Task(
                task_id=rt.task_id,
                func=rt.func,
                args=[],  # Not available in ReservedTask
                kwargs={},  # Not available in ReservedTask
                created_at=rt.started_at,
                eta_at=None,
                expires_at=None,
                retry_count=0,
                max_retries=0,
                context=rt.context,
            )
            for rt in reserved_tasks
        ]

    async def update_task_state(self, task_id: str, **kwargs) -> None:
        """Patch a task row (e.g. next_run_time, retries)."""
        await self.initialize()

        if not kwargs:
            return

        # Build dynamic UPDATE query
        set_clauses = []
        values = []

        for key, value in kwargs.items():
            if key in ["retry_count", "max_retries"]:
                set_clauses.append(f"{key} = ?")
                values.append(value)
            elif key in ["eta_at", "expires_at"]:
                set_clauses.append(f"{key} = ?")
                values.append(value.isoformat() if value else None)

        if set_clauses:
            sql = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE task_id = ?"
            values.append(task_id)

            async with aiosqlite.connect(self.database_path) as db:
                await db.execute(sql, values)
                await db.commit()

    async def store_result(self, result: Result) -> None:
        """Persist a task result."""
        await self.initialize()

        async with aiosqlite.connect(self.database_path) as db:
            if result.error:
                await self.mark_failure(
                    result.task_id, result.error, result.traceback or ""
                )
            else:
                await self.mark_success(result.task_id, result.value or b"")

    async def claim_task(self, task_id: str, lock_timeout: int = 30) -> bool:
        """Atomically claim a task for processing."""
        await self.initialize()

        async with aiosqlite.connect(self.database_path) as db:
            # Try to update the task status to 'claimed' if it's still pending
            cursor = await db.execute(
                """
                UPDATE tasks 
                SET status = 'claimed', started_at = ?
                WHERE task_id = ? AND status = 'pending'
            """,
                (datetime.now(timezone.utc).isoformat(), task_id),
            )

            await db.commit()
            return cursor.rowcount > 0

    async def release_task(self, task_id: str) -> None:
        """Release lock for task_id (called when a worker aborts)."""
        await self.initialize()

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(
                """
                UPDATE tasks 
                SET status = 'pending', started_at = NULL
                WHERE task_id = ? AND status = 'claimed'
            """,
                (task_id,),
            )
            await db.commit()

    async def schedule_retry(self, task_id: str, delay: int) -> None:
        """Reschedule a failed task after delay seconds and bump retry counter."""
        await self.initialize()

        async with aiosqlite.connect(self.database_path) as db:
            # Calculate new ETA time and increment retry count
            new_eta = datetime.now(timezone.utc) + timedelta(seconds=delay)

            await db.execute(
                """
                UPDATE tasks 
                SET status = 'pending', 
                    eta_at = ?,
                    retry_count = retry_count + 1,
                    started_at = NULL,
                    completed_at = NULL
                WHERE task_id = ?
            """,
                (new_eta.isoformat(), task_id),
            )
            await db.commit()
