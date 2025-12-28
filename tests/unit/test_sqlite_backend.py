"""Tests for SQLite backend implementation."""

import asyncio
import tempfile
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

import pytest

from sitq.backends.sqlite import SQLiteBackend
from sitq.core import Task, Result, ReservedTask


@pytest.fixture
async def sqlite_backend():
    """Create a temporary SQLite backend for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        backend = SQLiteBackend(tmp.name)
        await backend.initialize()
        yield backend
        # Cleanup is handled by tempfile


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        task_id=str(uuid.uuid4()),
        func="test_function",
        args=[1, 2, 3],
        kwargs={"key": "value"},
        created_at=datetime.now(timezone.utc),
        eta_at=None,
        expires_at=None,
        retry_count=0,
        max_retries=3,
        context={"worker_id": "test_worker"},
    )


class TestSQLiteBackend:
    """Test cases for SQLiteBackend."""

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test database initialization."""
        import aiosqlite

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            backend = SQLiteBackend(tmp.name)
            await backend.initialize()

            # Check that tables were created
            async with aiosqlite.connect(tmp.name) as db:
                cursor = await db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"
                )
                result = await cursor.fetchone()
                assert result is not None
                assert result[0] == "tasks"

    @pytest.mark.asyncio
    async def test_enqueue_task(self, sqlite_backend, sample_task):
        """Test enqueuing a task."""
        await sqlite_backend.enqueue(sample_task)

        # Verify task was stored
        async with sqlite_backend._connect() as db:
            cursor = await db.execute(
                "SELECT task_id, status, created_at FROM tasks WHERE task_id = ?",
                (sample_task.task_id,),
            )
            result = await cursor.fetchone()
            assert result is not None
            assert result[0] == sample_task.task_id
            assert result[1] == "pending"

    @pytest.mark.asyncio
    async def test_reserve_tasks(self, sqlite_backend, sample_task):
        """Test reserving tasks for execution."""
        # Enqueue a task
        await sqlite_backend.enqueue(sample_task)

        # Reserve the task
        now = datetime.now(timezone.utc)
        reserved_tasks = await sqlite_backend.reserve(1, now)

        assert len(reserved_tasks) == 1
        reserved = reserved_tasks[0]
        assert isinstance(reserved, ReservedTask)
        assert reserved.task_id == sample_task.task_id
        assert reserved.func == sample_task.func
        assert reserved.context == sample_task.context
        assert reserved.started_at >= now

    @pytest.mark.asyncio
    async def test_reserve_with_eta(self, sqlite_backend):
        """Test that tasks with future ETA are not reserved."""
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        task = Task(
            task_id=str(uuid.uuid4()),
            func="test_function",
            args=[],
            kwargs={},
            created_at=datetime.now(timezone.utc),
            eta_at=future_time,
            expires_at=None,
            retry_count=0,
            max_retries=3,
            context={},
        )

        await sqlite_backend.enqueue(task)

        # Try to reserve - should not get the task
        now = datetime.now(timezone.utc)
        reserved_tasks = await sqlite_backend.reserve(1, now)
        assert len(reserved_tasks) == 0

    @pytest.mark.asyncio
    async def test_reserve_expired_tasks(self, sqlite_backend):
        """Test that expired tasks are not reserved."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        task = Task(
            task_id=str(uuid.uuid4()),
            func="test_function",
            args=[],
            kwargs={},
            created_at=datetime.now(timezone.utc),
            eta_at=None,
            expires_at=past_time,
            retry_count=0,
            max_retries=3,
            context={},
        )

        await sqlite_backend.enqueue(task)

        # Try to reserve - should not get the expired task
        now = datetime.now(timezone.utc)
        reserved_tasks = await sqlite_backend.reserve(1, now)
        assert len(reserved_tasks) == 0

    @pytest.mark.asyncio
    async def test_mark_success(self, sqlite_backend, sample_task):
        """Test marking a task as successful."""
        await sqlite_backend.enqueue(sample_task)

        # Reserve the task first
        now = datetime.now(timezone.utc)
        reserved_tasks = await sqlite_backend.reserve(1, now)
        assert len(reserved_tasks) == 1

        # Mark as successful
        result_value = b"success_result"
        await sqlite_backend.mark_success(sample_task.task_id, result_value)

        # Verify the result
        result = await sqlite_backend.get_result(sample_task.task_id)
        assert result is not None
        assert result.value == result_value
        assert result.error is None
        assert result.traceback is None

    @pytest.mark.asyncio
    async def test_mark_failure(self, sqlite_backend, sample_task):
        """Test marking a task as failed."""
        await sqlite_backend.enqueue(sample_task)

        # Reserve the task first
        now = datetime.now(timezone.utc)
        reserved_tasks = await sqlite_backend.reserve(1, now)
        assert len(reserved_tasks) == 1

        # Mark as failed
        error_msg = "Test error"
        traceback = "Test traceback"
        await sqlite_backend.mark_failure(sample_task.task_id, error_msg, traceback)

        # Verify the result
        result = await sqlite_backend.get_result(sample_task.task_id)
        assert result is not None
        assert result.value is None
        assert result.error == error_msg
        assert result.traceback == traceback

    @pytest.mark.asyncio
    async def test_get_result_not_found(self, sqlite_backend):
        """Test getting result for non-existent task."""
        result = await sqlite_backend.get_result("non_existent_id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_result_pending_task(self, sqlite_backend, sample_task):
        """Test getting result for pending task."""
        await sqlite_backend.enqueue(sample_task)

        result = await sqlite_backend.get_result(sample_task.task_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_pending_tasks(self, sqlite_backend):
        """Test getting pending tasks."""
        # Create multiple tasks
        tasks = []
        for i in range(3):
            task = Task(
                task_id=str(uuid.uuid4()),
                func=f"test_function_{i}",
                args=[i],
                kwargs={},
                created_at=datetime.now(timezone.utc),
                eta_at=None,
                expires_at=None,
                retry_count=0,
                max_retries=3,
                context={},
            )
            tasks.append(task)
            await sqlite_backend.enqueue(task)

        # Get pending tasks
        pending_tasks = []
        async for task in sqlite_backend.get_pending_tasks(limit=5):
            pending_tasks.append(task)

        assert len(pending_tasks) == 3
        task_ids = {task.task_id for task in pending_tasks}
        expected_ids = {task.task_id for task in tasks}
        assert task_ids == expected_ids

    @pytest.mark.asyncio
    async def test_get_expired_tasks(self, sqlite_backend):
        """Test getting expired tasks."""
        # Create an expired task
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        expired_task = Task(
            task_id=str(uuid.uuid4()),
            func="expired_function",
            args=[],
            kwargs={},
            created_at=datetime.now(timezone.utc),
            eta_at=None,
            expires_at=past_time,
            retry_count=0,
            max_retries=3,
            context={},
        )

        # Create a non-expired task
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        valid_task = Task(
            task_id=str(uuid.uuid4()),
            func="valid_function",
            args=[],
            kwargs={},
            created_at=datetime.now(timezone.utc),
            eta_at=None,
            expires_at=future_time,
            retry_count=0,
            max_retries=3,
            context={},
        )

        await sqlite_backend.enqueue(expired_task)
        await sqlite_backend.enqueue(valid_task)

        # Get expired tasks
        expired_tasks = []
        now = datetime.now(timezone.utc)
        async for task in sqlite_backend.get_expired_tasks(now):
            expired_tasks.append(task)

        assert len(expired_tasks) == 1
        assert expired_tasks[0].task_id == expired_task.task_id

    @pytest.mark.asyncio
    async def test_delete_task(self, sqlite_backend, sample_task):
        """Test deleting a task."""
        await sqlite_backend.enqueue(sample_task)

        # Verify task exists by checking database directly
        import aiosqlite

        async with aiosqlite.connect(sqlite_backend.database_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM tasks WHERE task_id = ?", (sample_task.task_id,)
            )
            count = await cursor.fetchone()
            assert count[0] == 1

        # Delete the task
        await sqlite_backend.delete_task(sample_task.task_id)

        # Verify task is gone
        async with aiosqlite.connect(sqlite_backend.database_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM tasks WHERE task_id = ?", (sample_task.task_id,)
            )
            count = await cursor.fetchone()
            assert count[0] == 0

    @pytest.mark.asyncio
    async def test_get_queue_stats(self, sqlite_backend):
        """Test getting queue statistics."""
        # Create tasks with different statuses
        pending_task = Task(
            task_id=str(uuid.uuid4()),
            func="pending_function",
            args=[],
            kwargs={},
            created_at=datetime.now(timezone.utc),
            eta_at=None,
            expires_at=None,
            retry_count=0,
            max_retries=3,
            context={},
        )

        await sqlite_backend.enqueue(pending_task)

        # Reserve a task
        reserved_tasks = await sqlite_backend.reserve(1, datetime.now(timezone.utc))
        assert len(reserved_tasks) == 1

        # Mark another task as successful
        success_task = Task(
            task_id=str(uuid.uuid4()),
            func="success_function",
            args=[],
            kwargs={},
            created_at=datetime.now(timezone.utc),
            eta_at=None,
            expires_at=None,
            retry_count=0,
            max_retries=3,
            context={},
        )
        await sqlite_backend.enqueue(success_task)
        await sqlite_backend.reserve(1, datetime.now(timezone.utc))
        await sqlite_backend.mark_success(success_task.task_id, b"success")

        # Mark another task as failed
        failed_task = Task(
            task_id=str(uuid.uuid4()),
            func="failed_function",
            args=[],
            kwargs={},
            created_at=datetime.now(timezone.utc),
            eta_at=None,
            expires_at=None,
            retry_count=0,
            max_retries=3,
            context={},
        )
        await sqlite_backend.enqueue(failed_task)
        await sqlite_backend.reserve(1, datetime.now(timezone.utc))
        await sqlite_backend.mark_failure(failed_task.task_id, "error", "traceback")

        # Get stats
        stats = await sqlite_backend.get_queue_stats()

        assert stats["pending"] >= 0
        assert stats["reserved"] >= 1
        assert stats["completed"] >= 1
        assert stats["failed"] >= 1

    @pytest.mark.asyncio
    async def test_concurrent_reservations(self, sqlite_backend):
        """Test that concurrent reservations don't duplicate tasks."""
        # Create a single task
        task = Task(
            task_id=str(uuid.uuid4()),
            func="concurrent_function",
            args=[],
            kwargs={},
            created_at=datetime.now(timezone.utc),
            eta_at=None,
            expires_at=None,
            retry_count=0,
            max_retries=3,
            context={},
        )
        await sqlite_backend.enqueue(task)

        # Try to reserve concurrently
        now = datetime.now(timezone.utc)
        results = await asyncio.gather(
            sqlite_backend.reserve(1, now),
            sqlite_backend.reserve(1, now),
            sqlite_backend.reserve(1, now),
        )

        # Only one should get the task
        total_reserved = sum(len(reserved) for reserved in results)
        assert total_reserved == 1

        # The task should be reserved by exactly one caller
        reserved_by_count = sum(1 for reserved in results if len(reserved) > 0)
        assert reserved_by_count == 1
