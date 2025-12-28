"""Simple test for SyncTaskQueue functionality."""

import asyncio
import tempfile
import threading
import time
import uuid
from datetime import datetime, timezone, timedelta

from src.sitq.backends.sqlite import SQLiteBackend
from src.sitq.sync import SyncTaskQueue
from src.sitq.worker import Worker


def test_sync_queue_basic():
    """Test basic SyncTaskQueue functionality."""
    # Create backend
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        backend = SQLiteBackend(tmp.name)

        # Test SyncTaskQueue as context manager
        with SyncTaskQueue(backend) as queue:
            print("✓ SyncTaskQueue started")

            # Start a worker in background
            worker = Worker(backend, max_concurrency=1, poll_interval=0.1)

            def run_worker():
                asyncio.run(worker.start())

            worker_thread = threading.Thread(target=run_worker, daemon=True)
            worker_thread.start()

            try:
                # Give worker time to start
                time.sleep(0.5)

                # Test enqueue
                def test_task():
                    return "Hello from sync queue!"

                task_id = queue.enqueue(test_task)
                print(f"✓ Task enqueued with ID: {task_id}")

                # Test get_result
                result = queue.get_result(task_id, timeout=5.0)
                print(f"✓ Task result: {result}")
                assert result == "Hello from sync queue!"
                print("✓ Basic SyncTaskQueue test passed!")
                return

            finally:
                # Stop worker
                stop_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(stop_loop)
                try:
                    stop_loop.run_until_complete(worker.stop())
                finally:
                    stop_loop.close()
                worker_thread.join(timeout=5.0)
                print("✓ Worker stopped")

        print("✓ SyncTaskQueue stopped")


def test_sync_queue_error_handling():
    """Test error handling in SyncTaskQueue."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        backend = SQLiteBackend(tmp.name)

        with SyncTaskQueue(backend) as queue:
            print("✓ SyncTaskQueue started for error test")

            # Start a worker in background
            worker = Worker(backend, max_concurrency=1, poll_interval=0.1)

            def run_worker():
                asyncio.run(worker.start())

            worker_thread = threading.Thread(target=run_worker, daemon=True)
            worker_thread.start()

            try:
                # Give worker time to start
                time.sleep(0.5)

                # Test with failing task
                def failing_task():
                    raise ValueError("Test error from sync queue")

                task_id = queue.enqueue(failing_task)
                print(f"✓ Failing task enqueued with ID: {task_id}")

                # Test get_result for failure - should raise exception
                try:
                    result = queue.get_result(task_id, timeout=5.0)
                    print("✗ Expected exception but got result:", result)
                    return
                except Exception as e:
                    print(f"✓ Task error captured: {e}")
                    assert "Test error from sync queue" in str(e)
                    print("✓ Error handling test passed!")
                    return

            finally:
                # Stop worker
                stop_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(stop_loop)
                try:
                    stop_loop.run_until_complete(worker.stop())
                finally:
                    stop_loop.close()
                worker_thread.join(timeout=5.0)
                print("✓ Worker stopped")

        print("✓ SyncTaskQueue stopped")


def test_sync_queue_eta():
    """Test ETA scheduling with SyncTaskQueue."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        backend = SQLiteBackend(tmp.name)

        with SyncTaskQueue(backend) as queue:
            print("✓ SyncTaskQueue started for ETA test")

            # Start a worker in background
            worker = Worker(backend, max_concurrency=1, poll_interval=0.1)

            def run_worker():
                asyncio.run(worker.start())

            worker_thread = threading.Thread(target=run_worker, daemon=True)
            worker_thread.start()

            try:
                # Give worker time to start
                time.sleep(0.5)

                # Test with future ETA
                def eta_task():
                    return "ETA task completed"

                future_time = datetime.now(timezone.utc) + timedelta(seconds=2)
                task_id = queue.enqueue(eta_task, eta=future_time)
                print(f"✓ ETA task enqueued with ID: {task_id}")

                # Should not complete immediately
                result = queue.get_result(task_id, timeout=1.0)
                if result is None:
                    print("✓ Task correctly delayed by ETA")
                else:
                    print("✗ Task executed too early")
                    return

                # Wait past ETA time
                time.sleep(2.5)
                result = queue.get_result(task_id, timeout=5.0)
                print(f"✓ ETA task result: {result}")
                assert result == "ETA task completed"
                print("✓ ETA scheduling test passed!")
                return

            finally:
                # Stop worker
                stop_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(stop_loop)
                try:
                    stop_loop.run_until_complete(worker.stop())
                finally:
                    stop_loop.close()
                worker_thread.join(timeout=5.0)
                print("✓ Worker stopped")

        print("✓ SyncTaskQueue stopped")


if __name__ == "__main__":
    print("Testing SyncTaskQueue...")
    test_sync_queue_basic()
    print()
    test_sync_queue_error_handling()
    print()
    test_sync_queue_eta()
    print("All SyncTaskQueue tests completed!")
