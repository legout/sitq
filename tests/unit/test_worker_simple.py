"""Simple test for Worker functionality."""

import asyncio
import tempfile
import time
import uuid
from datetime import datetime, timezone

from src.sitq.backends.sqlite import SQLiteBackend
from src.sitq.core import Task
from src.sitq.worker import Worker
from src.sitq.serialization import CloudpickleSerializer


async def test_worker_basic():
    """Test basic worker functionality."""
    # Create backend and serializer
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        backend = SQLiteBackend(tmp.name)
        serializer = CloudpickleSerializer()

        await backend.connect()

        # Create a simple task
        def test_task():
            return "Hello from worker!"

        task = Task(
            id=str(uuid.uuid4()),
            func=serializer.dumps(test_task),
            created_at=datetime.now(timezone.utc),
        )

        # Enqueue task
        await backend.enqueue(task)
        print("✓ Task enqueued")

        # Create and start worker
        worker = Worker(
            backend=backend, serializer=serializer, max_concurrency=1, poll_interval=0.1
        )

        print("✓ Worker created")

        # Start worker in background
        worker_task = asyncio.create_task(worker.start())

        try:
            # Wait for task to complete
            timeout = 5.0
            start_time = time.time()

            while time.time() - start_time < timeout:
                result = await backend.get_result(task.id)
                if result and result.status == "success":
                    completed_result = serializer.loads(result.value)
                    assert completed_result == "Hello from worker!"
                    print("✓ Task completed successfully")
                    print(f"  Result: {completed_result}")
                    return
                await asyncio.sleep(0.1)

            print("✗ Task did not complete within timeout")

        finally:
            await worker.stop()
            await worker_task
            await backend.close()
            print("✓ Worker stopped")


if __name__ == "__main__":
    asyncio.run(test_worker_basic())
