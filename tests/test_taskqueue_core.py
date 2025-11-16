"""
Unit tests for TaskQueue core functionality.
"""

import asyncio
import tempfile
from datetime import datetime, timezone, timedelta

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sitq.serialization import CloudpickleSerializer
from sitq.backends.sqlite import SQLiteBackend
from sitq.queue import TaskQueue
from sitq.result import Result


def test_result_model():
    """Test Result data model creation and status checking."""

    # Test successful result
    success_result = Result(
        task_id="test_task_1",
        status="success",
        value={"result": "data"},
        enqueued_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
    )

    assert success_result.task_id == "test_task_1"
    assert success_result.status == "success"
    assert success_result.is_success() is True
    assert success_result.is_failed() is False
    assert success_result.value == {"result": "data"}

    # Test failed result
    failed_result = Result(
        task_id="test_task_2",
        status="failed",
        error="Test error message",
        traceback="Test traceback",
        enqueued_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
    )

    assert failed_result.task_id == "test_task_2"
    assert failed_result.status == "failed"
    assert failed_result.is_success() is False
    assert failed_result.is_failed() is True
    assert failed_result.error == "Test error message"
    assert failed_result.traceback == "Test traceback"


async def test_enqueue_immediate_task():
    """Test enqueueing a task with immediate availability."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)

        serializer = CloudpickleSerializer()
        task_queue = TaskQueue(backend, serializer)

        # Enqueue a task with immediate availability (eta=None)
        def test_function(x, y):
            return x + y

        task_id = await task_queue.enqueue(test_function, 5, 10)

        # Verify task was created and returned valid ID
        assert isinstance(task_id, str)
        assert len(task_id) > 0

        # Verify task is stored in backend

        # Check that the task was persisted
        conn = await backend._get_connection()
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
        assert row[2] == "pending"  # Status should be pending

        # Verify task is available immediately (available_at should be close to now)
        available_at = datetime.fromisoformat(row[3])
        now = datetime.now(timezone.utc)
        time_diff = abs((available_at - now).total_seconds())
        assert time_diff < 5  # Within 5 seconds

        await task_queue.close()


async def test_enqueue_delayed_task():
    """Test enqueueing a task with delayed availability."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)

        serializer = CloudpickleSerializer()
        task_queue = TaskQueue(backend, serializer)

        # Enqueue a task with future availability
        def test_function(x):
            return x * 2

        future_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        task_id = await task_queue.enqueue(test_function, 3, eta=future_time)

        # Verify task was created
        assert isinstance(task_id, str)

        # Verify task is stored with correct available_at time
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

        await task_queue.close()


async def test_task_serialization():
    """Test that tasks are properly serialized and can be reconstructed."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)

        serializer = CloudpickleSerializer()
        task_queue = TaskQueue(backend, serializer)

        # Create a test function and enqueue it
        def complex_function(a, b, *, c=10, d="test"):
            return {"sum": a + b, "product": a * b, "c": c, "d": d}

        task_id = await task_queue.enqueue(complex_function, 5, 7, c=20, d="complex")

        # Reserve the task and verify payload can be deserialized
        reserved_tasks = await backend.reserve(1, datetime.now(timezone.utc))
        assert len(reserved_tasks) == 1

        reserved_task = reserved_tasks[0]
        assert reserved_task.task_id == task_id

        # Deserialize and verify payload structure
        payload = serializer.loads(reserved_task.payload)
        assert callable(payload["func"])  # Should be callable
        assert payload["args"] == (5, 7)
        assert payload["kwargs"] == {"c": 20, "d": "complex"}

        # Verify the function works the same
        result = payload["func"](*payload["args"], **payload["kwargs"])
        expected = complex_function(5, 7, c=20, d="complex")
        assert result == expected

        await task_queue.close()


async def test_get_result_with_backend():
    """Test that get_result works with the backend to retrieve results."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)

        serializer = CloudpickleSerializer()
        task_queue = TaskQueue(backend, serializer)

        # Enqueue and reserve a task
        task_id = await task_queue.enqueue(lambda x: x * 2, 5)
        reserved_tasks = await backend.reserve(1, datetime.now(timezone.utc))

        assert len(reserved_tasks) == 1

        # Simulate task completion
        await backend.mark_success(
            task_id, "completed_result", datetime.now(timezone.utc)
        )

        # Retrieve result through TaskQueue
        result = await task_queue.get_result(task_id)

        assert result is not None
        assert result.__class__.__name__ == "Result"  # Check class name instead
        assert result.task_id == task_id
        assert result.status == "success"
        assert result.value == "completed_result"
        assert result.is_success() is True

        await task_queue.close()


async def test_get_result_timeout():
    """Test get_result timeout behavior."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)

        serializer = CloudpickleSerializer()
        task_queue = TaskQueue(backend, serializer)

        # Try to get result for non-existent task with short timeout
        result = await task_queue.get_result("nonexistent_task", timeout=0.1)
        assert result is None

        # Enqueue a task but don't complete it
        task_id = await task_queue.enqueue(lambda x: x, 1)

        # Try to get result with very short timeout
        result = await task_queue.get_result(task_id, timeout=0.1)
        assert result is None  # Should be None because task not completed

        await task_queue.close()


async def test_queue_close():
    """Test that closing the queue properly closes the backend."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)

        serializer = CloudpickleSerializer()
        task_queue = TaskQueue(backend, serializer)

        # Enqueue a task to verify functionality before close
        task_id = await task_queue.enqueue(lambda x: x, 1)
        assert isinstance(task_id, str)

        # Close the queue
        await task_queue.close()

        # Backend should be closed (can't test directly, but no exception should be raised)
        # This test mainly verifies no exception is raised during close


async def test_multiple_task_enqueue():
    """Test enqueueing multiple tasks and verifying they can be distinguished."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)

        serializer = CloudpickleSerializer()
        task_queue = TaskQueue(backend, serializer)

        # Enqueue multiple tasks
        task_ids = []
        for i in range(3):
            task_id = await task_queue.enqueue(lambda x: x + i, i)
            task_ids.append(task_id)

        # Verify all task IDs are unique
        assert len(task_ids) == 3
        assert len(set(task_ids)) == 3  # All unique

        # Verify all tasks are in the backend
        for task_id in task_ids:
            conn = await backend._get_connection()
            cursor = conn.execute(
                """
                SELECT task_id FROM tasks WHERE task_id = ?
            """,
                (task_id,),
            )

            row = cursor.fetchone()
            assert row is not None
            assert row[0] == task_id

        await task_queue.close()


async def run_all_tests():
    """Run all tests."""
    print("Running TaskQueue core tests...")

    # Test synchronous functionality
    print("Testing Result model...")
    test_result_model()
    print("✓ Result model test passed")

    # Test async functionality
    async_tests = [
        test_enqueue_immediate_task,
        test_enqueue_delayed_task,
        test_task_serialization,
        test_get_result_with_backend,
        test_get_result_timeout,
        test_queue_close,
        test_multiple_task_enqueue,
    ]

    for test_func in async_tests:
        print(f"Running {test_func.__name__}...")
        await test_func()
        print(f"✓ {test_func.__name__} passed")

    print("All TaskQueue core tests passed!")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
