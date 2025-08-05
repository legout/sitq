#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
sqlite_task_queue – a tiny, pure‑Python task queue backed by SQLite.

New in this version
-------------------
* Scheduling helpers: `enqueue_in`, `enqueue_at`, `enqueue_interval`, `enqueue_cron`.
* Columns `repeat_type`, `repeat_interval`, `cron_expression` added to the table.
* Automatic rescheduling of interval and cron jobs after a successful ``ack``.
* Optional cron support via the external ``croniter`` package.

Only the Python standard library is required for all features **except** cron
expressions – if you need cron you must install ``croniter``:

    pip install croniter
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, List, Optional, Union

# --------------------------------------------------------------------------- #
# Optional import for cron handling
# --------------------------------------------------------------------------- #
try:
    from croniter import croniter  # type: ignore
except Exception:  # pragma: no cover
    croniter = None  # will be checked when a cron job is scheduled


# --------------------------------------------------------------------------- #
# Helper dataclass – one row from the ``tasks`` table
# --------------------------------------------------------------------------- #
@dataclass
class Task:
    id: int
    queue: str
    payload: Any
    status: str
    attempts: int
    max_attempts: int
    created_at: int
    updated_at: int
    scheduled_at: Optional[int]
    reserved_at: Optional[int]
    worker_id: Optional[str]
    error_message: Optional[str]

    # New repeat‐related fields
    repeat_type: Optional[str] = None  # None | "interval" | "cron"
    repeat_interval: Optional[int] = None  # seconds – only for interval
    cron_expression: Optional[str] = None  # only for cron

    # ------------------------------------------------------------------- #
    # Convenience helpers
    # ------------------------------------------------------------------- #
    @property
    def age_seconds(self) -> int:
        """How many seconds have elapsed since the task was created."""
        return int(time.time() - self.created_at)

    @property
    def is_ready(self) -> bool:
        """True if this task can be dequeued now."""
        now = int(time.time())
        return self.status == "queued" and (
            self.scheduled_at is None or self.scheduled_at <= now
        )

    def __repr__(self) -> str:
        repeat = (
            f", repeat={self.repeat_type}"
            f"{'(' + str(self.repeat_interval) + 's)' if self.repeat_type == 'interval' else ''}"
            f"{'(' + self.cron_expression + ')' if self.repeat_type == 'cron' else ''}"
        )
        return (
            f"<Task id={self.id} q={self.queue!r} status={self.status!r} "
            f"attempts={self.attempts}/{self.max_attempts}{repeat} payload={self.payload!r}>"
        )


# --------------------------------------------------------------------------- #
# Core library – ``TaskQueue``
# --------------------------------------------------------------------------- #
class TaskQueue:
    """
    SQLite‑backed task queue with optional scheduling.

    Parameters
    ----------
    db_path : str | Path
        Path to the SQLite database file.  If the file does not exist it is created.
    auto_create : bool, default True
        If True the schema (including new repeat‑type columns) is created
        automatically.
    """

    def __init__(self, db_path: str | Path, *, auto_create: bool = True) -> None:
        self.db_path = Path(db_path)
        self._conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        if auto_create:
            self._init_schema()

    # ------------------------------------------------------------------- #
    # Schema creation / migration
    # ------------------------------------------------------------------- #
    def _init_schema(self) -> None:
        """
        Create the ``tasks`` table if it does not exist and add the columns
        needed for recurring jobs.  The migration is deliberately simple –
        it only adds the columns if they are missing.
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            queue TEXT NOT NULL,
            payload TEXT NOT NULL,
            status TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 5,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            scheduled_at INTEGER,
            reserved_at INTEGER,
            worker_id TEXT,
            error_message TEXT,
            repeat_type TEXT,          -- NULL, 'interval', 'cron'
            repeat_interval INTEGER,   -- seconds (used when repeat_type='interval')
            cron_expression TEXT       -- cron string (used when repeat_type='cron')
        );
        """
        self._conn.executescript(create_table_sql)

        # Ensure indexes for the common query patterns
        self._conn.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_queue_status
                ON tasks (queue, status);
            CREATE INDEX IF NOT EXISTS idx_tasks_scheduled_at
                ON tasks (scheduled_at);
            CREATE INDEX IF NOT EXISTS idx_tasks_repeat_type
                ON tasks (repeat_type);
            """
        )
        self._conn.commit()

        # ------- Migration: add columns if they were missing in older DBs -----
        # SQLite does not have IF NOT EXISTS for ALTER COLUMN, so we check PRAGMA.
        cur = self._conn.execute("PRAGMA table_info(tasks);")
        existing_cols = {row["name"] for row in cur.fetchall()}
        needed = {"repeat_type", "repeat_interval", "cron_expression"}
        for col in needed - existing_cols:
            try:
                self._conn.execute(f"ALTER TABLE tasks ADD COLUMN {col} TEXT;")
            except sqlite3.OperationalError:
                # Some SQLite versions may raise “duplicate column name” –
                # ignore because the column is already there.
                pass
        self._conn.commit()

    # ------------------------------------------------------------------- #
    # Helper – current Unix timestamp (seconds)
    # ------------------------------------------------------------------- #
    @staticmethod
    def _now_ts() -> int:
        return int(time.time())

    # ------------------------------------------------------------------- #
    # Core API – ENQUEUE (generic low‑level)
    # ------------------------------------------------------------------- #
    def enqueue(
        self,
        payload: Any,
        *,
        queue: str = "default",
        scheduled_at: Optional[int] = None,
        max_attempts: int = 5,
        repeat_type: Optional[str] = None,
        repeat_interval: Optional[int] = None,
        cron_expression: Optional[str] = None,
    ) -> int:
        """
        Insert a new task row.

        Returns
        -------
        int
            The auto‑generated ``id`` of the new task.
        """
        now = self._now_ts()
        payload_json = json.dumps(payload)

        sql = """
        INSERT INTO tasks (
            queue,
            payload,
            status,
            attempts,
            max_attempts,
            created_at,
            updated_at,
            scheduled_at,
            repeat_type,
            repeat_interval,
            cron_expression
        ) VALUES (?, ?, 'queued', 0, ?, ?, ?, ?, ?, ?, ?);
        """
        cur = self._conn.execute(
            sql,
            (
                queue,
                payload_json,
                max_attempts,
                now,
                now,
                scheduled_at,
                repeat_type,
                repeat_interval,
                cron_expression,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    # ------------------------------------------------------------------- #
    # Scheduling convenience helpers
    # ------------------------------------------------------------------- #
    def enqueue_in(
        self,
        payload: Any,
        *,
        delay: int,
        queue: str = "default",
        max_attempts: int = 5,
    ) -> int:
        """
        Schedule ``payload`` to run ``delay`` seconds from now.
        """
        if delay < 0:
            raise ValueError("delay must be non‑negative")
        scheduled_at = self._now_ts() + delay
        return self.enqueue(
            payload,
            queue=queue,
            scheduled_at=scheduled_at,
            max_attempts=max_attempts,
        )

    def enqueue_at(
        self,
        payload: Any,
        *,
        at: Union[int, datetime],
        queue: str = "default",
        max_attempts: int = 5,
    ) -> int:
        """
        Schedule ``payload`` to run at a concrete Unix timestamp or ``datetime``.
        """
        if isinstance(at, datetime):
            scheduled_at = int(at.timestamp())
        else:
            scheduled_at = int(at)
        if scheduled_at < self._now_ts():
            raise ValueError("scheduled time must be in the future")
        return self.enqueue(
            payload,
            queue=queue,
            scheduled_at=scheduled_at,
            max_attempts=max_attempts,
        )

    def enqueue_interval(
        self,
        payload: Any,
        *,
        interval: int,
        queue: str = "default",
        max_attempts: int = 5,
        initial_delay: int = 0,
    ) -> int:
        """
        Schedule a recurring job that runs every ``interval`` seconds.

        The first execution occurs after ``initial_delay`` seconds (defaults to 0).
        """
        if interval <= 0:
            raise ValueError("interval must be > 0")
        scheduled_at = self._now_ts() + initial_delay
        return self.enqueue(
            payload,
            queue=queue,
            scheduled_at=scheduled_at,
            max_attempts=max_attempts,
            repeat_type="interval",
            repeat_interval=interval,
        )

    def enqueue_cron(
        self,
        payload: Any,
        *,
        cron: str,
        queue: str = "default",
        max_attempts: int = 5,
        start_at: Optional[Union[int, datetime]] = None,
    ) -> int:
        """
        Schedule a recurring job using a *cron* expression (e.g. ``"*/5 * * * *"``).

        The next run time is calculated from ``start_at`` (default = now).  Requires
        the optional third‑party ``croniter`` package.
        """
        if croniter is None:
            raise RuntimeError(
                "Cron scheduling requires the 'croniter' package. Install with:\n"
                "    pip install croniter"
            )
        base_ts = self._now_ts()
        if start_at is not None:
            base_ts = int(
                start_at.timestamp() if isinstance(start_at, datetime) else start_at
            )

        # Compute the first occurrence *after* the base timestamp.
        itr = croniter(cron, datetime.utcfromtimestamp(base_ts))
        next_dt = itr.get_next(datetime)
        scheduled_at = int(next_dt.timestamp())

        return self.enqueue(
            payload,
            queue=queue,
            scheduled_at=scheduled_at,
            max_attempts=max_attempts,
            repeat_type="cron",
            cron_expression=cron,
        )

    # ------------------------------------------------------------------- #
    # CORE API – DEQUEUE (atomic claim)
    # ------------------------------------------------------------------- #
    def dequeue(
        self,
        *,
        queue: str = "default",
        worker_id: Optional[str] = None,
        visibility_timeout: int = 3600,
    ) -> Optional[Task]:
        """
        Atomically claim the next ready task from *queue*.

        Returns the ``Task`` instance or ``None`` if the queue is empty.
        """
        if worker_id is None:
            worker_id = str(uuid.uuid4())
        now = self._now_ts()

        try:
            cur = self._conn.cursor()
            cur.execute("BEGIN IMMEDIATE;")  # acquire write lock early

            claim_sql = """
            UPDATE tasks
            SET
                status = 'processing',
                reserved_at = ?,
                worker_id = ?,
                updated_at = ?
            WHERE id = (
                SELECT id FROM tasks
                WHERE queue = ?
                  AND status = 'queued'
                  AND (scheduled_at IS NULL OR scheduled_at <= ?)
                ORDER BY
                    COALESCE(scheduled_at, 0) ASC,
                    created_at ASC
                LIMIT 1
            );
            """
            cur.execute(
                claim_sql,
                (now, worker_id, now, queue, now),
            )
            if cur.rowcount == 0:
                # Nothing to claim – roll back
                cur.execute("ROLLBACK;")
                return None

            # Return the claimed row
            cur.execute(
                "SELECT * FROM tasks WHERE id = (SELECT MAX(id) FROM tasks WHERE worker_id = ? AND status = 'processing');",
                (worker_id,),
            )
            row = cur.fetchone()
            cur.execute("COMMIT;")
        except sqlite3.Error as exc:
            self._conn.rollback()
            raise RuntimeError(f"Failed to dequeue task: {exc}") from exc

        if row is None:
            return None

        return self._row_to_task(row)

    # ------------------------------------------------------------------- #
    # CORE API – ACKNOWLEDGE (with automatic reschedule for repeats)
    # ------------------------------------------------------------------- #
    def ack(self, task_id: int) -> None:
        """
        Mark a task as completed.

        * For one‑off jobs the status becomes ``complete``.
        * For recurring jobs (interval / cron) the next scheduled time is
          computed and the task is placed back into ``queued`` with ``attempts = 0``.
        """
        now = self._now_ts()
        task = self._get_task(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} does not exist")
        if task.status != "processing":
            raise ValueError(f"Task {task_id} is not in processing state – cannot ack")

        if task.repeat_type in (None, ""):
            # ONE‑OFF job
            sql = "UPDATE tasks SET status='complete', updated_at=? WHERE id=?;"
            self._conn.execute(sql, (now, task_id))
        else:
            # RECURRING job – compute the next run time
            next_ts = self._next_scheduled_at(task, now)
            sql = """
            UPDATE tasks
            SET
                status='queued',
                attempts=0,
                scheduled_at=?,
                updated_at=?,
                reserved_at=NULL,
                worker_id=NULL
            WHERE id=? AND status='processing';
            """
            self._conn.execute(sql, (next_ts, now, task_id))
        self._conn.commit()

    # ------------------------------------------------------------------- #
    # CORE API – FAIL (retries, eventual dead‑letter)
    # ------------------------------------------------------------------- #
    def fail(self, task_id: int, error_message: Optional[str] = None) -> None:
        """
        Record a failure for a task.

        * ``attempts`` is incremented.
        * If ``attempts`` reaches ``max_attempts`` the task moves to ``failed``.
        * Otherwise it is re‑queued (status = 'queued') for another try.
        * Repeat‑type information is preserved – a recurring job will
          continue to run on its next scheduled time after a successful run.
        """
        now = self._now_ts()
        sql = """
        UPDATE tasks
        SET
            attempts = attempts + 1,
            status = CASE WHEN (attempts + 1) >= max_attempts THEN 'failed' ELSE 'queued' END,
            error_message = ?,
            updated_at = ?,
            reserved_at = NULL,
            worker_id = NULL
        WHERE id = ? AND status = 'processing';
        """
        cur = self._conn.execute(sql, (error_message, now, task_id))
        if cur.rowcount == 0:
            raise ValueError(f"Task {task_id} is not in processing state – cannot fail")
        self._conn.commit()

    # ------------------------------------------------------------------- #
    # CORE API – REQUEUE STALE TASKS (visibility timeout)
    # ------------------------------------------------------------------- #
    def requeue_stale(self, visibility_timeout: int = 3600) -> int:
        """
        Find tasks that have been in ``processing`` longer than
        ``visibility_timeout`` seconds and put them back into ``queued``.
        Returns the number of rows affected.
        """
        cutoff = self._now_ts() - visibility_timeout
        sql = """
        UPDATE tasks
        SET
            status = 'queued',
            reserved_at = NULL,
            worker_id = NULL,
            updated_at = ?
        WHERE status = 'processing' AND reserved_at <= ?;
        """
        cur = self._conn.execute(sql, (self._now_ts(), cutoff))
        affected = cur.rowcount
        if affected:
            self._conn.commit()
        return affected

    # ------------------------------------------------------------------- #
    # METRICS / HELPERS
    # ------------------------------------------------------------------- #
    def count(self, *, queue: str = "default", status: Optional[str] = None) -> int:
        """Return the number of rows matching the filter."""
        sql = "SELECT COUNT(*) FROM tasks WHERE queue = ?"
        args: List[Any] = [queue]
        if status:
            sql += " AND status = ?"
            args.append(status)
        cur = self._conn.execute(sql, args)
        return
