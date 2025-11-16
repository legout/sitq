"""
Integration tests for Worker core functionality.
"""

import asyncio
import tempfile
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sitq.serialization import CloudpickleSerializer
from sitq.backends.sqlite import SQLiteBackend
from sitq.worker import Worker
from sitq.queue import TaskQueue


async def test_worker_basic_execution():
    """Test basic worker execution with both async and sync functions."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        # Test async function
        async def async_add(a, b):
            await asyncio.sleep(0.1)  # Simulate some async work
            return a + b

        # Test sync function
        def sync_multiply(x, y):
            time.sleep(0.1)  # Simulate some sync work
            return x * y

        # Enqueue tasks
        task_queue = TaskQueue(backend, serializer)
        async_task_id = await task_queue.enqueue(async_add, 5, 10)
        sync_task_id = await task_queue.enqueue(sync_multiply, 3, 7)

        # Start worker
        worker = Worker(backend, serializer, concurrency=2)
        await worker.start()

        # Wait for tasks to be processed
        await asyncio.sleep(1.0)

        # Check results
        async_result = await task_queue.get_result(async_task_id)
        sync_result = await task_queue.get_result(sync_task_id)

        assert async_result is not None
        assert async_result.status == "success"
        assert async_result.value == 15

        assert sync_result is not None
        assert sync_result.status == "success"
        assert sync_result.value == 21

        await worker.stop()
        print("✓ Basic execution test passed")


async def test_worker_concurrency():
    """Test worker concurrency control."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        # Create tasks that take some time to complete
        def slow_task(task_id, duration):
            time.sleep(duration)
            return f"completed_{task_id}"

        # Enqueue multiple tasks
        task_queue = TaskQueue(backend, serializer)
        task_ids = []
        for i in range(5):
            task_id = await task_queue.enqueue(slow_task, i, 0.2)  # 200ms each
            task_ids.append(task_id)

        # Start worker with concurrency=2
        worker = Worker(backend, serializer, concurrency=2)
        await worker.start()

        # Wait for all tasks to be processed (should take ~500ms with concurrency=2)
        await asyncio.sleep(1.5)

        # Check all results
        for i, task_id in enumerate(task_ids):
            result = await task_queue.get_result(task_id)
            assert result is not None
            assert result.status == "success"
            assert result.value == f"completed_{i}"

        await worker.stop()
        print("✓ Concurrency test passed")


async def test_worker_eta_scheduling():
    """Test worker handling of delayed (ETA) tasks."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        # Create immediate and delayed tasks
        def immediate_task():
            return "immediate"

        def delayed_task():
            return "delayed"

        task_queue = TaskQueue(backend, serializer)

        # Enqueue immediate task
        immediate_task_id = await task_queue.enqueue(immediate_task)

        # Enqueue delayed task (5 seconds in the future)
        future_time = datetime.now(timezone.utc) + timedelta(seconds=2)
        delayed_task_id = await task_queue.enqueue(delayed_task, eta=future_time)

        # Start worker
        worker = Worker(backend, serializer, concurrency=1)
        await worker.start()

        # Wait a bit for immediate task to be processed
        await asyncio.sleep(0.5)

        # Check immediate task is done
        immediate_result = await task_queue.get_result(immediate_task_id)
        assert immediate_result is not None
        assert immediate_result.status == "success"
        assert immediate_result.value == "immediate"

        # Check delayed task is not ready yet
        delayed_result = await task_queue.get_result(delayed_task_id)
        assert delayed_result is None  # Not ready yet

        # Wait for delayed task to become available
        await asyncio.sleep(2.5)

        # Check delayed task is now done
        delayed_result = await task_queue.get_result(delayed_task_id)
        assert delayed_result is not None
        assert delayed_result.status == "success"
        assert delayed_result.value == "delayed"

        await worker.stop()
        print("✓ ETA scheduling test passed")


async def test_worker_failure_handling():
    """Test worker handling of failing tasks."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        # Create functions that fail in different ways
        def sync_error():
            raise ValueError("Sync error message")

        async def async_error():
            await asyncio.sleep(0.1)
            raise TypeError("Async error message")

        def divide_by_zero():
            return 1 / 0

        # Enqueue failing tasks
        task_queue = TaskQueue(backend, serializer)
        sync_error_id = await task_queue.enqueue(sync_error)
        async_error_id = await task_queue.enqueue(async_error)
        divide_error_id = await task_queue.enqueue(divide_by_zero)

        # Start worker
        worker = Worker(backend, serializer, concurrency=3)
        await worker.start()

        # Wait for tasks to be processed
        await asyncio.sleep(1.0)

        # Check all tasks failed
        for task_id, expected_error in [
            (sync_error_id, "Sync error message"),
            (async_error_id, "Async error message"),
            (divide_error_id, "division by zero"),
        ]:
            result = await task_queue.get_result(task_id)
            assert result is not None
            assert result.status == "failed"
            assert expected_error in result.error
            assert result.traceback is not None
            assert "Error" in result.traceback

        await worker.stop()
        print("✓ Failure handling test passed")


async def test_worker_graceful_shutdown():
    """Test graceful worker shutdown with in-flight tasks."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        # Create a slow task
        def slow_task():
            time.sleep(0.5)  # Takes 500ms
            return "slow_completed"

        # Enqueue tasks
        task_queue = TaskQueue(backend, serializer)
        task_ids = []
        for i in range(3):
            task_id = await task_queue.enqueue(slow_task)
            task_ids.append(task_id)

        # Start worker
        worker = Worker(backend, serializer, concurrency=2, poll_interval=0.1)
        await worker.start()

        # Wait a bit for tasks to start
        await asyncio.sleep(0.2)

        # Stop worker while tasks are still running
        await worker.stop()

        # Check that no tasks are left in in_progress state
        conn = await backend._get_connection()
        cursor = conn.execute(
            """
            SELECT COUNT(*) FROM tasks 
            WHERE status = 'in_progress' AND task_id IN ({})
        """.format(",".join("?" * len(task_ids))),
            task_ids,
        )

        in_progress_count = cursor.fetchone()[0]
        assert in_progress_count == 0, "Some tasks were left in in_progress state"

        print("✓ Graceful shutdown test passed")


async def test_worker_context_manager():
    """Test worker as async context manager."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        # Create a simple task
        def simple_task():
            return "simple"

        # Enqueue task
        task_queue = TaskQueue(backend, serializer)
        task_id = await task_queue.enqueue(simple_task)

        # Use worker as context manager
        async with Worker(backend, serializer) as worker:
            assert worker._running
            await asyncio.sleep(0.5)  # Let it process

        assert not worker._running

        # Check task was processed
        result = await task_queue.get_result(task_id)
        assert result is not None
        assert result.status == "success"
        assert result.value == "simple"

        print("✓ Context manager test passed")


async def test_worker_logging():
    """Test worker logging functionality."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        # Create custom logger for loguru
        import io

        log_capture_string = io.StringIO()

        # Configure a logger that writes to our capture string
        class TestLogger:
            def __init__(self, capture_stream):
                self.capture = capture_stream
                self.level = "INFO"

            def info(self, msg):
                self.capture.write(f"INFO:{msg}\n")
                self.capture.flush()

            def debug(self, msg):
                self.capture.write(f"DEBUG:{msg}\n")
                self.capture.flush()

            def error(self, msg):
                self.capture.write(f"ERROR:{msg}\n")
                self.capture.flush()

            def warning(self, msg):
                self.capture.write(f"WARNING:{msg}\n")
                self.capture.flush()

        test_logger = TestLogger(log_capture_string)

        # Create tasks
        def success_task():
            return "success"

        def error_task():
            raise ValueError("Expected error")

        # Enqueue tasks
        task_queue = TaskQueue(backend, serializer)
        await task_queue.enqueue(success_task)
        await task_queue.enqueue(error_task)

        # Start worker with test logger
        worker = Worker(backend, serializer, custom_logger=test_logger)
        await worker.start()

        # Wait for processing
        await asyncio.sleep(1.0)

        await worker.stop()

        # Check log output
        log_contents = log_capture_string.getvalue()

        # Check for expected log messages
        assert "Worker started" in log_contents
        assert "Starting task" in log_contents
        assert "completed successfully" in log_contents
        assert "failed" in log_contents

        print("✓ Logging test passed")


async def test_worker_no_tasks():
    """Test worker behavior when no tasks are available."""

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        backend = SQLiteBackend(db_path)
        serializer = CloudpickleSerializer()

        # Start worker without any tasks
        worker = Worker(backend, serializer, poll_interval=0.1)
        await worker.start()

        # Let it run for a short time
        await asyncio.sleep(0.5)

        # Stop worker
        await worker.stop()

        # Should complete without errors
        print("✓ No tasks test passed")


async def run_all_tests():
    """Run all worker tests."""
    print("Running Worker core tests...")

    tests = [
        test_worker_basic_execution,
        test_worker_concurrency,
        test_worker_eta_scheduling,
        test_worker_failure_handling,
        test_worker_graceful_shutdown,
        test_worker_context_manager,
        test_worker_logging,
        test_worker_no_tasks,
    ]

    for test in tests:
        try:
            print(f"Running {test.__name__}...")
            await test()
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            raise

    print("All Worker core tests passed!")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
