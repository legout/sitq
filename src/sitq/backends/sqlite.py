"""
SQLiteBackend implementation for persistent task storage.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Any

from .base import Backend, ReservedTask, Result


class SQLiteBackend(Backend):
    """
    SQLite-based backend for task persistence.

    Uses a local SQLite database file to store tasks and results.
    Supports WAL mode for concurrent access by multiple workers.
    """

    def __init__(self, database_path: str | Path, serializer=None):
        """
        Initialize SQLite backend.

        Args:
            database_path: Path to the SQLite database file
            serializer: Serializer for result values. If None, will use cloudpickle.
        """
        self.database_path = Path(database_path)
        self._conn: Optional[sqlite3.Connection] = None
        if serializer is None:
            # Import here to avoid circular imports
            from ..serialization import CloudpickleSerializer

            serializer = CloudpickleSerializer()
        self.serializer = serializer

    async def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection with proper configuration."""
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(self.database_path), check_same_thread=False
            )
            # Enable WAL mode for better concurrency
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            # Set timeout for database locks
            self._conn.execute("PRAGMA busy_timeout=30000")
            self._create_tables()
        return self._conn

    def _create_tables(self) -> None:
        """Create the tasks table if it doesn't exist."""
        conn = self._conn
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                payload BLOB NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('pending', 'in_progress', 'success', 'failed')),
                available_at TIMESTAMP NOT NULL,
                started_at TIMESTAMP,
                finished_at TIMESTAMP,
                result_value BLOB,
                error_message TEXT,
                traceback TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    async def enqueue(
        self, task_id: str, payload: bytes, available_at: datetime
    ) -> None:
        """Persist a new task with pending status."""
        conn = await self._get_connection()

        # Convert datetime to ISO format for SQLite
        available_at_str = available_at.replace(tzinfo=timezone.utc).isoformat()

        conn.execute(
            """
            INSERT INTO tasks (task_id, payload, status, available_at)
            VALUES (?, ?, 'pending', ?)
        """,
            (task_id, payload, available_at_str),
        )
        conn.commit()

    async def reserve(self, max_items: int, now: datetime) -> List[ReservedTask]:
        """Atomically reserve tasks for execution."""
        conn = await self._get_connection()

        now_str = now.replace(tzinfo=timezone.utc).isoformat()
        started_at_str = datetime.now(timezone.utc).isoformat()

        # Use a transaction to atomically reserve tasks
        try:
            conn.execute("BEGIN IMMEDIATE")

            # Update tasks and return updated rows
            cursor = conn.execute(
                """
                UPDATE tasks 
                SET status = 'in_progress', started_at = ?
                WHERE task_id IN (
                    SELECT task_id 
                    FROM tasks 
                    WHERE status = 'pending' AND available_at <= ?
                    ORDER BY available_at ASC
                    LIMIT ?
                )
                RETURNING task_id, payload, started_at
            """,
                (started_at_str, now_str, max_items),
            )

            rows = cursor.fetchall()
            conn.commit()

            # Convert rows to ReservedTask objects
            return [
                ReservedTask(
                    task_id=row[0],
                    payload=row[1],
                    started_at=datetime.fromisoformat(row[2]),
                )
                for row in rows
            ]
        except sqlite3.Error:
            conn.execute("ROLLBACK")
            raise

    async def mark_success(
        self, task_id: str, value: Any, finished_at: datetime
    ) -> None:
        """Mark a task as successfully completed."""
        conn = await self._get_connection()

        finished_at_str = finished_at.replace(tzinfo=timezone.utc).isoformat()

        # Serialize the result value
        serialized_value = self.serializer.dumps(value)

        conn.execute(
            """
            UPDATE tasks 
            SET status = 'success', result_value = ?, finished_at = ?
            WHERE task_id = ?
        """,
            (serialized_value, finished_at_str, task_id),
        )
        conn.commit()

    async def mark_failure(
        self, task_id: str, error: str, traceback: Optional[str], finished_at: datetime
    ) -> None:
        """Mark a task as failed."""
        conn = await self._get_connection()

        finished_at_str = finished_at.replace(tzinfo=timezone.utc).isoformat()

        conn.execute(
            """
            UPDATE tasks 
            SET status = 'failed', error_message = ?, traceback = ?, finished_at = ?
            WHERE task_id = ?
        """,
            (error, traceback, finished_at_str, task_id),
        )
        conn.commit()

    async def get_result(self, task_id: str) -> Optional[Result]:
        """Retrieve the result of a completed task."""
        conn = await self._get_connection()

        cursor = conn.execute(
            """
            SELECT task_id, status, result_value, error_message, traceback, finished_at
            FROM tasks 
            WHERE task_id = ? AND status IN ('success', 'failed')
        """,
            (task_id,),
        )

        row = cursor.fetchone()
        if row is None:
            return None

        return Result(
            task_id=row[0],
            status=row[1],
            value=row[2],
            error=row[3],
            traceback=row[4],
            finished_at=datetime.fromisoformat(row[5]) if row[5] else None,
        )

    async def close(self) -> None:
        """Close database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
