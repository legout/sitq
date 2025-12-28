#!/usr/bin/env python3
"""Simpler standalone test to verify worker dispatch works."""

import asyncio
import tempfile

from sitq import Worker, TaskQueue, SQLiteBackend
from sitq.serialization import CloudpickleSerializer


async def test_basic_dispatch():
    """Test basic task dispatching."""
    # Use temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    backend = SQLiteBackend(db_path)
    await backend.connect()
    queue = TaskQueue(backend)
    serializer = CloudpickleSerializer()

    async def simple_task(value):
        print(f"  Task {value} started")
        await asyncio.sleep(0.1)
        print(f"  Task {value} completed")
        return value

    # Enqueue 3 tasks
    print("Enqueueing 3 tasks...")
    task_ids = []
    for i in range(3):
        task_id = await queue.enqueue(simple_task, i)
        task_ids.append(task_id)
        print(f"  Enqueued task {task_id}")

    # Create worker with max_concurrency=2
    print("\nStarting worker with max_concurrency=2...")
    worker = Worker(backend, max_concurrency=2, poll_interval=0.01)

    # Start worker in background
    worker_task = asyncio.create_task(worker.start())

    # Wait for tasks to complete
    print("\nWaiting for tasks to complete...")
    task_results = []
    for task_id in task_ids:
        result = await queue.get_result(task_id, timeout=5.0)
        if result and result.value:
            task_results.append(serializer.loads(result.value))

    # Stop worker
    print("\nStopping worker...")
    await worker.stop()
    await worker_task

    # Verify results
    print(f"\nResults from queue: {task_results}")
    assert sorted(task_results) == [0, 1, 2], (
        f"Expected [0, 1, 2], got {sorted(task_results)}"
    )

    print("\n✓ Test passed: Worker correctly dispatched tasks!")

    # Cleanup
    await backend.close()
    import os

    os.unlink(db_path)


if __name__ == "__main__":
    asyncio.run(test_basic_dispatch())
