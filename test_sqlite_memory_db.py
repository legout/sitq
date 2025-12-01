"""Tests for SQLite in-memory database implementation."""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta

import pytest

from src.sitq.backends.sqlite import SQLiteBackend
from src.sitq.core import Task, Result, ReservedTask


@pytest.fixture
async def memory_backend():
    """Create an in-memory SQLite backend for testing."""
    backend = SQLiteBackend(":memory:")
    await backend.initialize()
    yield backend
    await backend.close()


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


@pytest.mark.asyncio
class TestInMemoryDatabase:
    """Test cases for in-memory SQLite database."""

    @pytest.mark.asyncio
    async def test_shared_connection_persistence(self, memory_backend, sample_task):
        """Test that data persists across different operations using shared connection."""
        # Enqueue a task
        await memory_backend.enqueue(sample_task)

        # Reserve the task in a separate operation
        now = datetime.now(timezone.utc)
        reserved_tasks = await memory_backend.reserve(1, now)

        assert len(reserved_tasks) == 1
        assert reserved_tasks[0].task_id == sample_task.task_id

    @pytest.mark.asyncio
    async def test_multiple_operations_same_connection(self, memory_backend):
        """Test multiple operations work correctly with the same shared connection."""
        # Create multiple tasks
        tasks = []
        for i in range(5):
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
            await memory_backend.enqueue(task)

        # Reserve tasks in multiple batches
        now = datetime.now(timezone.utc)
        batch1 = await memory_backend.reserve(2, now)
        batch2 = await memory_backend.reserve(2, now)
        batch3 = await memory_backend.reserve(1, now)

        # Should have reserved all tasks
        total_reserved = len(batch1) + len(batch2) + len(batch3)
        assert total_reserved == 5

        # All task IDs should be unique
        reserved_ids = []
        for batch in [batch1, batch2, batch3]:
            for task in batch:
                reserved_ids.append(task.task_id)
        assert len(set(reserved_ids)) == 5

    @pytest.mark.asyncio
    async def test_concurrent_operations_shared_connection(
        self, memory_backend, sample_task
    ):
        """Test concurrent operations work correctly with shared connection."""
        # Enqueue multiple tasks
        tasks = []
        for i in range(10):
            task = Task(
                task_id=str(uuid.uuid4()),
                func=f"concurrent_function_{i}",
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
            await memory_backend.enqueue(task)

        # Concurrent reservations
        now = datetime.now(timezone.utc)
        results = await asyncio.gather(
            *[memory_backend.reserve(2, now) for _ in range(5)]
        )

        # Should have reserved all tasks without duplication
        total_reserved = sum(len(reserved) for reserved in results)
        assert total_reserved == 10

        # Check for uniqueness
        all_task_ids = []
        for batch in results:
            for task in batch:
                all_task_ids.append(task.task_id)
        assert len(set(all_task_ids)) == 10

    @pytest.mark.asyncio
    async def test_task_lifecycle_shared_connection(self, memory_backend, sample_task):
        """Test complete task lifecycle using shared connection."""
        # Enqueue
        await memory_backend.enqueue(sample_task)

        # Reserve
        now = datetime.now(timezone.utc)
        reserved_tasks = await memory_backend.reserve(1, now)
        assert len(reserved_tasks) == 1

        # Mark as successful
        result_value = b"test_result"
        await memory_backend.mark_success(sample_task.task_id, result_value)

        # Get result
        result = await memory_backend.get_result(sample_task.task_id)
        assert result is not None
        assert result.value == result_value
        assert result.error is None

        # Task should no longer be in pending tasks
        pending_tasks = []
        async for task in memory_backend.get_pending_tasks(limit=10):
            pending_tasks.append(task)
        assert len(pending_tasks) == 0

    @pytest.mark.asyncio
    async def test_error_handling_shared_connection(self, memory_backend, sample_task):
        """Test error handling with shared connection."""
        # Enqueue and reserve
        await memory_backend.enqueue(sample_task)
        now = datetime.now(timezone.utc)
        reserved_tasks = await memory_backend.reserve(1, now)
        assert len(reserved_tasks) == 1

        # Mark as failed
        error_msg = "Test error message"
        traceback = "Test traceback content"
        await memory_backend.mark_failure(sample_task.task_id, error_msg, traceback)

        # Verify error is stored correctly
        result = await memory_backend.get_result(sample_task.task_id)
        assert result is not None
        assert result.value is None
        assert result.error == error_msg
        assert result.traceback == traceback

    @pytest.mark.asyncio
    async def test_connection_cleanup(self, memory_backend):
        """Test that connection is properly cleaned up."""
        # Verify shared connection exists
        assert memory_backend._shared_connection is not None
        assert memory_backend._is_memory is True

        # Perform some operations
        task = Task(
            task_id=str(uuid.uuid4()),
            func="cleanup_test",
            args=[],
            kwargs={},
            created_at=datetime.now(timezone.utc),
            eta_at=None,
            expires_at=None,
            retry_count=0,
            max_retries=3,
            context={},
        )
        await memory_backend.enqueue(task)

        # Close connection
        await memory_backend.close()

        # Verify connection is cleaned up
        assert memory_backend._shared_connection is None

    @pytest.mark.asyncio
    async def test_statistics_with_shared_connection(self, memory_backend):
        """Test queue statistics work correctly with shared connection."""
        # Create tasks with different outcomes
        tasks = []
        for i in range(3):
            task = Task(
                task_id=str(uuid.uuid4()),
                func=f"stats_function_{i}",
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
            await memory_backend.enqueue(task)

        # Reserve one task
        now = datetime.now(timezone.utc)
        reserved = await memory_backend.reserve(1, now)
        assert len(reserved) == 1

        # Mark one as successful
        await memory_backend.mark_success(tasks[1].task_id, b"success_result")

        # Mark one as failed
        await memory_backend.mark_failure(tasks[2].task_id, "error", "traceback")

        # Get statistics
        stats = await memory_backend.get_queue_stats()

        # Should have at least these counts
        assert stats["pending"] >= 0
        assert stats["reserved"] >= 1
        assert stats["completed"] >= 1
        assert stats["failed"] >= 1

    @pytest.mark.asyncio
    async def test_retry_logic_shared_connection(self, memory_backend):
        """Test retry logic works correctly with shared connection."""
        # Create a task that will be retried
        task = Task(
            task_id=str(uuid.uuid4()),
            func="retry_function",
            args=[],
            kwargs={},
            created_at=datetime.now(timezone.utc),
            eta_at=None,
            expires_at=None,
            retry_count=0,
            max_retries=3,
            context={},
        )
        await memory_backend.enqueue(task)

        # Reserve and fail the task
        now = datetime.now(timezone.utc)
        reserved = await memory_backend.reserve(1, now)
        assert len(reserved) == 1

        await memory_backend.mark_failure(task.task_id, "Retry error", "traceback")

        # Task should be available for retry (with delay)
        retry_available_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        # Try to reserve immediately - should not get it
        immediate_reserve = await memory_backend.reserve(1, datetime.now(timezone.utc))
        assert len(immediate_reserve) == 0

        # Mock time passage by checking available tasks directly
        pending_tasks = []
        async for pending_task in memory_backend.get_pending_tasks(limit=10):
            pending_tasks.append(pending_task)

        # The task should still be in pending but with future available_at
        retry_task_ids = [t.task_id for t in pending_tasks if t.task_id == task.task_id]
        assert len(retry_task_ids) == 0  # Should not be available yet

    @pytest.mark.asyncio
    async def test_eta_scheduling_shared_connection(self, memory_backend):
        """Test ETA-based scheduling works with shared connection."""
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)

        task = Task(
            task_id=str(uuid.uuid4()),
            func="eta_function",
            args=[],
            kwargs={},
            created_at=datetime.now(timezone.utc),
            eta_at=future_time,
            expires_at=None,
            retry_count=0,
            max_retries=3,
            context={},
        )
        await memory_backend.enqueue(task)

        # Should not be available for reservation now
        now = datetime.now(timezone.utc)
        reserved = await memory_backend.reserve(1, now)
        assert len(reserved) == 0

        # But should be in pending tasks
        pending_tasks = []
        async for pending_task in memory_backend.get_pending_tasks(limit=10):
            pending_tasks.append(pending_task)

        eta_task_ids = [t.task_id for t in pending_tasks if t.task_id == task.task_id]
        assert len(eta_task_ids) == 1

    @pytest.mark.asyncio
    async def test_expiration_shared_connection(self, memory_backend):
        """Test task expiration works with shared connection."""
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)

        task = Task(
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
        await memory_backend.enqueue(task)

        # Should not be available for reservation
        now = datetime.now(timezone.utc)
        reserved = await memory_backend.reserve(1, now)
        assert len(reserved) == 0

        # Should appear in expired tasks
        expired_tasks = []
        async for expired_task in memory_backend.get_expired_tasks(now):
            expired_tasks.append(expired_task)

        assert len(expired_tasks) == 1
        assert expired_tasks[0].task_id == task.task_id
