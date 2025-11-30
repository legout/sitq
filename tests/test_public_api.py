"""
Tests for the public API surface of sitq.

This module tests that the public API imports work correctly and that
a basic enqueue/worker/result flow functions as expected when using
the top-level sitq package imports.
"""

import asyncio
import tempfile
from pathlib import Path

# Test public API imports
from sitq import TaskQueue, SyncTaskQueue, Worker, Result
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer


async def test_public_api_imports():
    """Test that all public API symbols can be imported from sitq package."""

    # These imports should not raise any exceptions
    assert TaskQueue is not None
    assert SyncTaskQueue is not None
    assert Worker is not None
    assert Result is not None

    print("✓ All public API imports successful")


async def test_public_api_basic_flow():
    """Test basic enqueue/worker/result flow using public API imports."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        # Create task functions
        async def async_add(a, b):
            await asyncio.sleep(0.01)  # Simulate some async work
            return a + b

        def sync_multiply(x, y):
            return x * y

        # Set up TaskQueue using public API
        queue = TaskQueue(backend, serializer)

        # Enqueue tasks using public API
        async_task_id = await queue.enqueue(async_add, 5, 10)
        sync_task_id = await queue.enqueue(sync_multiply, 3, 7)

        # Verify task IDs are returned
        assert isinstance(async_task_id, str)
        assert len(async_task_id) > 0
        assert isinstance(sync_task_id, str)
        assert len(sync_task_id) > 0
        assert async_task_id != sync_task_id

        # Start Worker using public API
        worker = Worker(backend, serializer, concurrency=2)
        await worker.start()

        # Wait for tasks to be processed
        await asyncio.sleep(0.5)

        # Get results using public API
        async_result = await queue.get_result(async_task_id, timeout=5)
        sync_result = await queue.get_result(sync_task_id, timeout=5)

        # Verify results using public API Result class
        assert async_result is not None
        assert isinstance(async_result, Result)
        assert async_result.is_success()
        assert async_result.value == 15

        assert sync_result is not None
        assert isinstance(sync_result, Result)
        assert sync_result.is_success()
        assert sync_result.value == 21

        await worker.stop()
        await queue.close()

        print("✓ Basic flow test passed")


def test_sync_api_basic_flow():
    """Test basic flow using SyncTaskQueue from public API."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        def add_function(a, b):
            return a + b

        # Use SyncTaskQueue from public API
        with SyncTaskQueue(backend, serializer) as queue:
            # Enqueue task
            task_id = queue.enqueue(add_function, 10, 20)
            assert isinstance(task_id, str)
            assert len(task_id) > 0

            # Simulate task completion in the background
            from datetime import datetime, timezone

            asyncio.run(backend.mark_success(task_id, 30, datetime.now(timezone.utc)))

            # Get result
            result = queue.get_result(task_id, timeout=1)

            # Verify result
            assert result is not None
            assert isinstance(result, Result)
            assert result.is_success()
            assert result.value == 30

        print("✓ Sync API flow test passed")


async def test_public_api_result_methods():
    """Test Result class methods from public API."""

    # Test successful result
    success_result = Result(
        task_id="test_success",
        status="success",
        value={"data": "test"},
        error=None,
        traceback=None,
    )

    assert success_result.is_success()
    assert not success_result.is_failed()

    # Test failed result
    failed_result = Result(
        task_id="test_failed",
        status="failed",
        value=None,
        error="Test error",
        traceback="Error details",
    )

    assert not failed_result.is_success()
    assert failed_result.is_failed()

    print("✓ Result methods test passed")


def run_all_tests():
    """Run all public API tests."""
    print("Running public API tests...")

    # Test imports
    asyncio.run(test_public_api_imports())

    # Test basic flow
    asyncio.run(test_public_api_basic_flow())

    # Test sync flow (run outside async context)
    test_sync_api_basic_flow()

    # Test Result methods
    asyncio.run(test_public_api_result_methods())

    print("All public API tests passed!")


if __name__ == "__main__":
    run_all_tests()
