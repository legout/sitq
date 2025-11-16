"""
Unit and integration tests for SQLiteBackend.
"""

import asyncio
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sitq.backends.sqlite import SQLiteBackend


async def test_backend_protocol_interface():
    """Test that SQLiteBackend implements the Backend protocol correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)

        # Test that all required methods exist
        assert hasattr(backend, "enqueue")
        assert hasattr(backend, "reserve")
        assert hasattr(backend, "mark_success")
        assert hasattr(backend, "mark_failure")
        assert hasattr(backend, "get_result")
        assert hasattr(backend, "close")

        # Test that methods are async
        assert asyncio.iscoroutinefunction(backend.enqueue)
        assert asyncio.iscoroutinefunction(backend.reserve)
        assert asyncio.iscoroutinefunction(backend.mark_success)
        assert asyncio.iscoroutinefunction(backend.mark_failure)
        assert asyncio.iscoroutinefunction(backend.get_result)
        assert asyncio.iscoroutinefunction(backend.close)

        await backend.close()


async def test_create_tables_on_first_use():
    """Test that tables are created on first backend use."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)

        # Verify database file doesn't exist yet
        assert not db_path.exists()

        # Initialize backend (should create tables)
        await backend._get_connection()

        # Verify database file and table were created
        assert db_path.exists()

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='tasks'
        """)
        assert cursor.fetchone() is not None

        conn.close()
        await backend.close()


async def test_enqueue_task():
    """Test task enqueueing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)

        task_id = "test_task_1"
        payload = b"test_payload"
        available_at = datetime.now(timezone.utc)

        await backend.enqueue(task_id, payload, available_at)

        # Verify task was persisted
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            """
            SELECT task_id, payload, status, available_at 
            FROM tasks 
            WHERE task_id = ?
        """,
            (task_id,),
        )

        row = cursor.fetchone()
        assert row is not None
        assert row[0] == task_id
        assert row[1] == payload
        assert row[2] == "pending"

        conn.close()
        await backend.close()


async def test_reserve_available_task():
    """Test reserving an available task."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)

        # Enqueue a task with current time
        task_id = "test_task_1"
        payload = b"test_payload"
        now = datetime.now(timezone.utc)
        await backend.enqueue(task_id, payload, now)

        # Reserve the task
        reserved = await backend.reserve(1, now)

        # Verify reservation
        assert len(reserved) == 1
        reserved_task = reserved[0]
        assert reserved_task.task_id == task_id
        assert reserved_task.payload == payload
        assert reserved_task.started_at is not None

        # Verify task status was updated
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute(
            """
            SELECT status, started_at FROM tasks WHERE task_id = ?
        """,
            (task_id,),
        )

        row = cursor.fetchone()
        assert row[0] == "in_progress"
        assert row[1] is not None

        conn.close()
        await backend.close()


async def test_reserve_future_task():
    """Test that future tasks are not reserved."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)

        # Enqueue a task with future availability
        task_id = "test_task_1"
        payload = b"test_payload"
        now = datetime.now(timezone.utc)
        future_time = now.replace(second=now.second + 10)
        await backend.enqueue(task_id, payload, future_time)

        # Try to reserve tasks with current time
        reserved = await backend.reserve(1, now)

        # Should return no tasks
        assert len(reserved) == 0

        await backend.close()


async def test_mark_success():
    """Test marking a task as successful."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)

        # Enqueue and reserve a task
        task_id = "test_task_1"
        payload = b"test_payload"
        now = datetime.now(timezone.utc)
        await backend.enqueue(task_id, payload, now)
        await backend.reserve(1, now)

        # Mark as successful
        result_value = "success_result"
        finished_at = datetime.now(timezone.utc)
        await backend.mark_success(task_id, result_value, finished_at)

        # Verify completion
        result = await backend.get_result(task_id)
        assert result is not None
        assert result.task_id == task_id
        assert result.status == "success"
        assert result.value == result_value
        assert result.finished_at is not None

        await backend.close()


async def test_mark_failure():
    """Test marking a task as failed."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)

        # Enqueue and reserve a task
        task_id = "test_task_1"
        payload = b"test_payload"
        now = datetime.now(timezone.utc)
        await backend.enqueue(task_id, payload, now)
        await backend.reserve(1, now)

        # Mark as failed
        error_msg = "Test error"
        traceback = "Test traceback"
        finished_at = datetime.now(timezone.utc)
        await backend.mark_failure(task_id, error_msg, traceback, finished_at)

        # Verify failure
        result = await backend.get_result(task_id)
        assert result is not None
        assert result.task_id == task_id
        assert result.status == "failure"
        assert result.error == error_msg
        assert result.traceback == traceback
        assert result.finished_at is not None

        await backend.close()


async def test_get_result_missing_task():
    """Test getting result for a task that doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)

        # Try to get result for non-existent task
        result = await backend.get_result("nonexistent_task")

        # Should return None
        assert result is None

        await backend.close()


async def test_get_result_pending_task():
    """Test getting result for a task that's still pending."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)

        # Enqueue a task but don't reserve it
        task_id = "test_task_1"
        payload = b"test_payload"
        now = datetime.now(timezone.utc)
        await backend.enqueue(task_id, payload, now)

        # Try to get result for pending task
        result = await backend.get_result(task_id)

        # Should return None (only completed tasks return results)
        assert result is None

        await backend.close()


async def test_wal_mode_configuration():
    """Test that WAL mode is enabled for SQLite connections."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)

        await backend._get_connection()

        # Check WAL mode is enabled
        cursor = backend._conn.execute("PRAGMA journal_mode")
        result = cursor.fetchone()[0].lower()
        assert result == "wal"

        await backend.close()


async def test_multiple_reservations():
    """Test reserving multiple tasks at once."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)

        # Enqueue multiple tasks
        now = datetime.now(timezone.utc)
        tasks = []
        for i in range(3):
            task_id = f"task_{i}"
            payload = f"payload_{i}".encode()
            await backend.enqueue(task_id, payload, now)
            tasks.append((task_id, payload))

        # Reserve up to 2 tasks
        reserved = await backend.reserve(2, now)

        # Should have 2 reserved tasks
        assert len(reserved) == 2

        # Verify the reserved tasks
        reserved_ids = {task.task_id for task in reserved}
        assert len(reserved_ids) == 2  # No duplicates

        await backend.close()


async def run_all_tests():
    """Run all tests."""
    tests = [
        test_backend_protocol_interface,
        test_create_tables_on_first_use,
        test_enqueue_task,
        test_reserve_available_task,
        test_reserve_future_task,
        test_mark_success,
        test_mark_failure,
        test_get_result_missing_task,
        test_get_result_pending_task,
        test_wal_mode_configuration,
        test_multiple_reservations,
    ]

    for test in tests:
        print(f"Running {test.__name__}...")
        try:
            await test()
            print(f"✓ {test.__name__} passed")
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())
