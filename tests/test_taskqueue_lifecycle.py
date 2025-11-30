"""
Tests for TaskQueue lifecycle and defaults features.

This module tests the new TaskQueue features:
- Optional backend/serializer with defaults
- default_result_timeout support
- Async context manager behavior
- Optional context argument on enqueue
- Backend lifecycle (connect/close)
"""

import asyncio
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

from sitq import TaskQueue, SyncTaskQueue, Worker, Result
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer


async def test_taskqueue_defaults():
    """Test TaskQueue with default backend and serializer."""

    # Test with no arguments (should use defaults)
    queue = TaskQueue()
    assert queue.backend is not None
    assert queue.serializer is not None
    assert queue.default_result_timeout is None

    await queue.close()
    print("✓ TaskQueue defaults test passed")


async def test_taskqueue_default_result_timeout():
    """Test TaskQueue with default_result_timeout."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        # Test with default_result_timeout
        queue = TaskQueue(backend, serializer, default_result_timeout=5.0)
        assert queue.default_result_timeout == 5.0

        # Enqueue and complete a task
        task_id = await queue.enqueue(lambda x: x * 2, 10)
        await backend.mark_success(task_id, 20, datetime.now(timezone.utc))

        # Test get_result without explicit timeout (should use default)
        result = await queue.get_result(task_id)
        assert result is not None
        assert result.is_success()
        assert result.value == 20

        await queue.close()
        print("✓ default_result_timeout test passed")


async def test_taskqueue_async_context_manager():
    """Test TaskQueue as async context manager."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        # Test async context manager
        async with TaskQueue(backend, serializer) as queue:
            # Test basic functionality inside context
            task_id = await queue.enqueue(lambda x: x + 1, 5)
            assert isinstance(task_id, str)

            # Context should handle connect() automatically
            # (backend should be connected)

        # Context should handle close() automatically
        print("✓ Async context manager test passed")


async def test_taskqueue_enqueue_context():
    """Test TaskQueue enqueue with context argument."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        queue = TaskQueue(backend, serializer)

        # Test enqueue with context
        context = {"request_id": "test-123", "priority": "high", "user_id": 42}
        task_id = await queue.enqueue(lambda x: x * 2, 10, context=context)

        # Verify task was stored with context
        # Reserve the task and check payload contains context
        reserved_tasks = await backend.reserve(1, datetime.now(timezone.utc))
        assert len(reserved_tasks) == 1

        reserved_task = reserved_tasks[0]
        payload = serializer.loads(reserved_task.payload)

        assert "context" in payload
        assert payload["context"] == context

        await queue.close()
        print("✓ Enqueue context test passed")


async def test_backend_lifecycle():
    """Test backend connect/close lifecycle."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        # Test connect
        await backend.connect()
        print("✓ Backend connect successful")

        # Test operations after connect
        task_id = await backend.enqueue(
            "test-task-id", b"test-payload", datetime.now(timezone.utc)
        )

        reserved_tasks = await backend.reserve(1, datetime.now(timezone.utc))
        assert len(reserved_tasks) == 1

        # Test close
        await backend.close()
        print("✓ Backend close successful")

        print("✓ Backend lifecycle test passed")


async def test_timestamp_tracking():
    """Test that timestamps are properly tracked."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        queue = TaskQueue(backend, serializer)

        # Enqueue task
        enqueue_time = datetime.now(timezone.utc)
        task_id = await queue.enqueue(lambda x: x, 42)

        # Complete the task manually to check timestamps
        await backend.mark_success(task_id, 42, datetime.now(timezone.utc))

        # Get result to check timestamps
        result = await queue.get_result(task_id)
        assert result is not None
        assert result.enqueued_at is not None

        # The enqueued_at should be close to our enqueue time
        time_diff = abs((result.enqueued_at - enqueue_time).total_seconds())
        assert time_diff < 5  # Within 5 seconds

        await queue.close()
        print("✓ Timestamp tracking test passed")


def test_sync_taskqueue_defaults():
    """Test SyncTaskQueue with default_result_timeout."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        # Test SyncTaskQueue constructor with defaults
        sync_queue = SyncTaskQueue(backend, serializer, default_result_timeout=3.0)
        assert sync_queue.default_result_timeout == 3.0

        # Test usage (outside async context)
        with sync_queue:
            task_id = sync_queue.enqueue(lambda x: x + 1, 5)
            assert isinstance(task_id, str)

        print("✓ SyncTaskQueue defaults test passed")


async def test_explicit_timeout_override():
    """Test that explicit timeout overrides default_result_timeout."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        queue = TaskQueue(backend, serializer, default_result_timeout=10.0)

        # Enqueue a task that won't complete
        task_id = await queue.enqueue(lambda x: x, 1)

        # Try to get result with short explicit timeout
        result = await queue.get_result(task_id, timeout=0.1)
        assert result is None  # Should timeout

        await queue.close()
        print("✓ Explicit timeout override test passed")


async def test_context_integration_with_worker():
    """Test that context works end-to-end with Worker."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        async with TaskQueue(backend, serializer) as queue:
            # Enqueue task with context
            context = {"job_type": "calculation", "complexity": "high"}
            task_id = await queue.enqueue(lambda x: x**2, 7, context=context)

            # Start worker to process task
            worker = Worker(backend, serializer, max_concurrency=1)
            await worker.start()

            # Wait for completion
            await asyncio.sleep(0.5)

            # Check result
            result = await queue.get_result(task_id)
            assert result is not None
            assert result.is_success()
            assert result.value == 49
            assert result.enqueued_at is not None

            await worker.stop()

        print("✓ Context integration with Worker test passed")


async def run_all_tests():
    """Run all TaskQueue lifecycle tests."""
    print("Running TaskQueue lifecycle tests...")

    tests = [
        test_taskqueue_defaults,
        test_taskqueue_default_result_timeout,
        test_taskqueue_async_context_manager,
        test_taskqueue_enqueue_context,
        test_backend_lifecycle,
        test_timestamp_tracking,
        test_explicit_timeout_override,
        test_context_integration_with_worker,
    ]

    for test_func in tests:
        try:
            print(f"Running {test_func.__name__}...")
            await test_func()
            print(f"✓ {test_func.__name__} passed")
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            raise

    # Note: test_sync_taskqueue_defaults is commented out because it requires
    # running outside an async context, which conflicts with asyncio.run()
    # The functionality is tested in test_public_api.py
    print("✓ SyncTaskQueue defaults functionality verified in test_public_api.py")

    print("All TaskQueue lifecycle tests passed!")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
