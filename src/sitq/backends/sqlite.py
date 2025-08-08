"""
SQLite‑based backend using SQLAlchemy async engine.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy import (
    Table,
    Column,
    String,
    DateTime,
    Integer,
    LargeBinary,
    Boolean,
    select,
    update,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection, AsyncEngine

from ..core import Task, Result, _now
from .base import Backend


class SQLiteBackend(Backend):
    """SQLite implementation – suitable for local development or testing."""

    def __init__(self, db_path: str = "sqlite+aiosqlite:///pytaskqueue.db"):
        self.db_path = self._gen_db_uri(db_path)
        self.engine: Optional[AsyncEngine] = None
        self._tasks: Optional[Table] = None
        self._results: Optional[Table] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def connect(self):
        """
        Create the async engine and configure SQLite pragmas for cross-process use
        (WAL mode and a reasonable busy timeout). We run the synchronous PRAGMA
        statements via AsyncConnection.run_sync before creating tables.
        """
        self.engine = create_async_engine(self.db_path, echo=False, future=True)
        async with self.engine.begin() as conn:
            # Configure PRAGMAs for better concurrency between processes, then
            # create tables if they don't exist.
            await conn.run_sync(self._configure_pragma)
            await conn.run_sync(self._create_tables)
        # Keep a short-lived connection available for callers that expect one.
        self.conn = await self.engine.connect()

    def _configure_pragma(self, sync_conn):
        """
        Configure SQLite PRAGMA settings on the synchronous connection provided
        by AsyncConnection.run_sync. Enabling WAL mode and a longer busy timeout
        improves visibility and reduces locking issues when multiple processes
        use the same SQLite file.
        """
        try:
            sync_conn.execute(sa.text("PRAGMA journal_mode=WAL"))
            sync_conn.execute(sa.text("PRAGMA synchronous=NORMAL"))
            sync_conn.execute(sa.text("PRAGMA busy_timeout=5000"))
        except Exception:
            # Non-fatal: if pragmas fail, proceed; table creation will still run.
            pass

    async def close(self):
        if self.engine:
            await self.engine.dispose()

    @staticmethod
    def _gen_db_uri(db_path: str) -> str:
        """Generate the database URI for SQLite."""
        if not db_path.startswith("sqlite+aiosqlite://"):
            return f"sqlite+aiosqlite:///{db_path}"
        return db_path

    # ------------------------------------------------------------------
    def _create_tables(self, sync_conn):
        # Diagnostic: log the actual type passed by AsyncConnection.run_sync
        print(f"_create_tables arg type: {type(sync_conn)}")

        # Build a fresh MetaData for the synchronous DDL operation
        metadata = sa.MetaData()

        # ------------------------------------------------------------------
        # tasks table – stores payload + coordination columns
        # ------------------------------------------------------------------
        tasks = Table(
            "tasks",
            metadata,
            Column("id", String, primary_key=True),
            Column("func", LargeBinary, nullable=False),
            Column("args", LargeBinary, nullable=True),
            Column("kwargs", LargeBinary, nullable=True),
            Column("context", LargeBinary, nullable=True),
            Column("schedule", String, nullable=True),
            Column("created_at", DateTime, default=sa.func.now()),
            Column("next_run_time", DateTime, nullable=True),
            Column("last_run_time", DateTime, nullable=True),
            Column("result_id", String, nullable=True),
            Column("retries", Integer, default=0),
            Column("max_retries", Integer, default=3),
            Column("locked_until", DateTime, nullable=True),
        )

        # ------------------------------------------------------------------
        # results table – immutable outcome records
        # ------------------------------------------------------------------
        results = Table(
            "results",
            metadata,
            Column("id", String, primary_key=True),
            Column("task_id", String, sa.ForeignKey("tasks.id")),
            Column("status", String, nullable=False),
            Column("value", LargeBinary, nullable=True),
            Column("traceback", String, nullable=True),
            Column("retry_count", Integer, default=0),
            Column("last_retry_at", DateTime, nullable=True),
        )

        # Execute create_all against the synchronous connection provided by run_sync
        metadata.create_all(bind=sync_conn)  # type: ignore[arg-type]

        # keep references for later use
        self._tasks = tasks
        self._results = results

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------
    async def enqueue(self, task: Task) -> None:
        stmt = self._tasks.insert().values(
            id=task.id,
            func=task.func,
            args=task.args,
            kwargs=task.kwargs,
            context=task.context,
            schedule=json.dumps(task.schedule) if task.schedule else None,
            created_at=task.created_at,
            next_run_time=task.next_run_time,
            last_run_time=task.last_run_time,
            result_id=task.result_id,
            retries=task.retries,
            max_retries=task.max_retries,
            locked_until=None,
        )
        async with (self.engine.begin() as conn):
            await conn.execute(stmt)

    async def fetch_due_tasks(self, limit: int = 1) -> List[Task]:
        now = _now()
        stmt = (
            select(self._tasks)
            .where(
                (
                    (self._tasks.c.next_run_time <= now)
                    | (self._tasks.c.next_run_time.is_(None))
                )
                & (
                    (self._tasks.c.locked_until.is_(None))
                    | (self._tasks.c.locked_until < now)
                )
                & (self._tasks.c.result_id.is_(None))
            )
            .order_by(self._tasks.c.next_run_time)
            .limit(limit)
        )
        # Use a short-lived connection for the read to avoid holding open a transaction
        async with self.engine.connect() as conn:
            result = await conn.execute(stmt)
            rows = result.fetchall()
        tasks: List[Task] = []
        for row in rows:
            tasks.append(
                Task(
                    id=row.id,
                    func=row.func,
                    args=row.args,
                    kwargs=row.kwargs,
                    context=row.context,
                    schedule=json.loads(row.schedule) if row.schedule else None,
                    created_at=row.created_at,
                    next_run_time=row.next_run_time,
                    last_run_time=row.last_run_time,
                    result_id=row.result_id,
                    retries=row.retries,
                    max_retries=row.max_retries,
                    locked_until=row.locked_until,
                )
            )
        return tasks

    async def update_task_state(self, task_id: str, **kwargs) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(
                self._tasks.update().where(self._tasks.c.id == task_id).values(**kwargs)
            )

    async def store_result(self, result: Result) -> None:
        stmt = self._results.insert().values(
            id=result.id,
            task_id=result.task_id,
            status=result.status,
            value=result.value,
            traceback=result.traceback,
            retry_count=result.retry_count,
            last_retry_at=result.last_retry_at,
        )
        async with self.engine.begin() as conn:
            await conn.execute(stmt)

    async def get_result(self, task_id: str) -> Optional[Result]:
        """
        Return the FINAL result for task_id, if available.

        We consult the tasks table's `result_id` column which is set only when
        a task reaches a terminal state. This avoids returning intermediate
        attempt rows from the immutable results table.
        """
        # First fetch the result_id referenced by the task (short-lived connection)
        stmt_task = select(self._tasks.c.result_id).where(self._tasks.c.id == task_id)
        async with self.engine.connect() as conn:
            task_res = await conn.execute(stmt_task)
            task_row = task_res.fetchone()

        if not task_row or not task_row.result_id:
            return None

        # Fetch the referenced result row
        stmt = select(self._results).where(self._results.c.id == task_row.result_id)
        async with self.engine.connect() as conn:
            result = await conn.execute(stmt)
            row = result.fetchone()

        if not row:
            return None

        return Result(
            id=row.id,
            task_id=row.task_id,
            status=row.status,
            value=row.value,
            traceback=row.traceback,
            retry_count=row.retry_count,
            last_retry_at=row.last_retry_at,
        )

    # ------------------------------------------------------------------
    # Locking / retry helpers
    # ------------------------------------------------------------------
    async def claim_task(self, task_id: str, lock_timeout: int = 30) -> bool:
        now = _now()
        lock_until = now + timedelta(seconds=lock_timeout)
        async with self.engine.begin() as conn:
            result = await conn.execute(
                self._tasks.update()
                .where(
                    (self._tasks.c.id == task_id)
                    & (
                        (self._tasks.c.locked_until.is_(None))
                        | (self._tasks.c.locked_until < now)
                    )
                )
                .values(locked_until=lock_until)
            )
            return result.rowcount > 0

    async def release_task(self, task_id: str) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(
                self._tasks.update()
                .where(self._tasks.c.id == task_id)
                .values(locked_until=None)
            )

    async def schedule_retry(self, task_id: str, delay: int) -> None:
        now = _now()
        retry_time = now + timedelta(seconds=delay)
        async with self.engine.begin() as conn:
            await conn.execute(
                self._tasks.update()
                .where(self._tasks.c.id == task_id)
                .values(
                    retries=self._tasks.c.retries + 1,
                    next_run_time=retry_time,
                    locked_until=None,
                )
            )
