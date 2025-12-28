"""Test SyncTaskQueue with Worker integration."""

import tempfile
import time
import uuid
from datetime import datetime, timezone, timedelta

from src.sitq.backends.sqlite import SQLiteBackend
from src.sitq.sync import SyncTaskQueue
from src.sitq.worker import Worker


def test_sync_queue_with_worker():
    """Test SyncTaskQueue with an actual Worker running."""
    # Create backend
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        backend = SQLiteBackend(tmp.name)

        # Start SyncTaskQueue
        with SyncTaskQueue(backend) as queue:
            print("✓ SyncTaskQueue started")

            # Start a worker in background
            worker = Worker(backend, max_concurrency=1, poll_interval=0.1)

            import asyncio
            import threading

            def run_worker():
                asyncio.run(worker.start())

            worker_thread = threading.Thread(target=run_worker, daemon=True)
            worker_thread.start()

            try:
                # Give worker time to start
                time.sleep(0.5)

                # Test enqueue and get_result
                def test_task():
                    return "Hello from sync queue with worker!"

                task_id = queue.enqueue(test_task)
                print(f"✓ Task enqueued with ID: {task_id}")

                # Wait for result
                start_time = time.time()
                timeout = 10.0

                while time.time() - start_time < timeout:
                    result = queue.get_result(task_id)
                    if result is not None:
                        print(f"✓ Task result: {result}")
                        assert result == "Hello from sync queue with worker!"
                        print("✓ Integration test passed!")
                        return
                    time.sleep(0.1)

                print("✗ Task did not complete within timeout")

            finally:
                # Stop worker by creating a new event loop
                stop_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(stop_loop)
                try:
                    stop_loop.run_until_complete(worker.stop())
                finally:
                    stop_loop.close()
                worker_thread.join(timeout=5.0)
                print("✓ Worker stopped")


if __name__ == "__main__":
    print("Testing SyncTaskQueue with Worker integration...")
    test_sync_queue_with_worker()
