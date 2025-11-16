"""
Unit tests for SyncTaskQueue synchronous wrapper functionality.
"""

import asyncio
import tempfile
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sitq.serialization import CloudpickleSerializer
from sitq.backends.sqlite import SQLiteBackend
from sitq.sync import SyncTaskQueue


def test_context_manager():
    """Test that SyncTaskQueue works as a context manager."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        # Test successful context manager usage
        with SyncTaskQueue(backend, serializer) as queue:
            assert hasattr(queue, "enqueue")
            assert hasattr(queue, "get_result")
            assert hasattr(queue, "close")

        print("✓ Context manager test passed")


def test_enqueue_and_get_result():
    """Test basic enqueue and get_result functionality."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        with SyncTaskQueue(backend, serializer) as queue:
            # Enqueue a task
            def test_function(a, b):
                return a + b

            task_id = queue.enqueue(test_function, 5, 10)
            assert isinstance(task_id, str)
            assert len(task_id) > 0

            # Simulate task completion
            async def complete_task():
                await backend.mark_success(task_id, 15, datetime.now(timezone.utc))

            asyncio.run(complete_task())

            # Get result
            result = queue.get_result(task_id)
            assert result is not None
            assert result.__class__.__name__ == "Result"
            assert result.status == "success"
            assert result.value == 15

        print("✓ Enqueue and get result test passed")


def test_delayed_task_scheduling():
    """Test enqueueing tasks with delayed ETA."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        with SyncTaskQueue(backend, serializer) as queue:
            # Enqueue a task with future ETA
            future_time = datetime.now(timezone.utc) + timedelta(minutes=5)
            task_id = queue.enqueue(lambda x: x * 2, 3, eta=future_time)

            assert isinstance(task_id, str)

            # Verify the task is stored with correct ETA
            async def check_eta():
                conn = await backend._get_connection()
                cursor = conn.execute(
                    """
                    SELECT available_at FROM tasks WHERE task_id = ?
                """,
                    (task_id,),
                )

                row = cursor.fetchone()
                assert row is not None

                stored_time = datetime.fromisoformat(row[0])
                time_diff = abs((stored_time - future_time).total_seconds())
                assert time_diff < 1  # Within 1 second

            asyncio.run(check_eta())

        print("✓ Delayed task scheduling test passed")


def test_timeout_behavior():
    """Test get_result timeout behavior."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        with SyncTaskQueue(backend, serializer) as queue:
            # Enqueue a task but don't complete it
            task_id = queue.enqueue(lambda x: x, 1)

            # Try to get result with very short timeout
            result = queue.get_result(task_id, timeout=0.1)
            assert result is None  # Should be None because task not completed

            # Try to get result for non-existent task
            result = queue.get_result("nonexistent", timeout=0.1)
            assert result is None

        print("✓ Timeout behavior test passed")


def test_multiple_tasks():
    """Test enqueueing and managing multiple tasks."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        with SyncTaskQueue(backend, serializer) as queue:
            # Enqueue multiple tasks
            task_ids = []
            for i in range(3):
                task_id = queue.enqueue(lambda x, i=i: x + i, 10)
                task_ids.append(task_id)

            # Verify all task IDs are unique
            assert len(task_ids) == 3
            assert len(set(task_ids)) == 3  # All unique

            # Complete all tasks
            async def complete_tasks():
                for i, task_id in enumerate(task_ids):
                    await backend.mark_success(
                        task_id, 10 + i, datetime.now(timezone.utc)
                    )

            asyncio.run(complete_tasks())

            # Get all results
            results = []
            for task_id in task_ids:
                result = queue.get_result(task_id)
                results.append(result)

            # Verify all results
            assert len(results) == 3
            for i, result in enumerate(results):
                assert result is not None
                assert result.status == "success"
                assert result.value == 10 + i

        print("✓ Multiple tasks test passed")


def test_error_handling():
    """Test error handling and failed tasks."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        with SyncTaskQueue(backend, serializer) as queue:
            # Enqueue a task
            task_id = queue.enqueue(lambda: 1 / 0)  # This will fail

            # Simulate task failure
            async def fail_task():
                await backend.mark_failure(
                    task_id,
                    "ZeroDivisionError",
                    "division by zero",
                    datetime.now(timezone.utc),
                )

            asyncio.run(fail_task())

            # Get result (should be failed)
            result = queue.get_result(task_id)
            assert result is not None
            assert result.status == "failed"
            assert result.error == "ZeroDivisionError"
            assert result.traceback == "division by zero"
            assert result.is_failed() is True

        print("✓ Error handling test passed")


def test_no_async_context_error():
    """Test that SyncTaskQueue detects when used in async context."""

    async def test_in_async():
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            backend = SQLiteBackend(db_path)
            serializer = CloudpickleSerializer()

            try:
                # This should raise an error because we're in an async context
                with SyncTaskQueue(backend, serializer) as queue:
                    pass
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "cannot be used inside an existing async context" in str(e)

    # Run the async test
    asyncio.run(test_in_async())
    print("✓ No async context error test passed")


def test_manual_close():
    """Test manual close functionality."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        # Test without context manager
        queue = SyncTaskQueue(backend, serializer)
        queue.close()  # Should not raise an error
        print("✓ Manual close test passed")


def test_complex_function():
    """Test with complex functions and data structures."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        with SyncTaskQueue(backend, serializer) as queue:
            # Test with complex function that returns a simple result
            def complex_function(data):
                # Return a simple string result instead of complex dict
                return f"processed {len(data['items'])} items"

            test_data = {"items": [1, 2, 3, 4, 5]}

            task_id = queue.enqueue(complex_function, test_data)

            # Complete the task
            async def complete_complex_task():
                expected_result = complex_function(test_data)
                await backend.mark_success(
                    task_id, expected_result, datetime.now(timezone.utc)
                )

            asyncio.run(complete_complex_task())

            # Get and verify result
            result = queue.get_result(task_id)
            assert result is not None
            assert result.status == "success"
            assert result.value == "processed 5 items"

        print("✓ Complex function test passed")


def run_all_tests():
    """Run all tests."""
    print("Running SyncTaskQueue tests...")

    tests = [
        test_context_manager,
        test_enqueue_and_get_result,
        test_delayed_task_scheduling,
        test_timeout_behavior,
        test_multiple_tasks,
        test_error_handling,
        test_no_async_context_error,
        test_manual_close,
        test_complex_function,
    ]

    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            raise

    print("All SyncTaskQueue tests passed!")


if __name__ == "__main__":
    run_all_tests()
