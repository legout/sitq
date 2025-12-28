#!/usr/bin/env python3
"""Standalone test to verify worker concurrency fix."""

import asyncio
import tempfile
from datetime import datetime, timezone

from sitq import Worker, TaskQueue, SQLiteBackend


async def test_concurrency_bounded():
    """Test that worker respects max_concurrency."""
    # Use temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    backend = SQLiteBackend(db_path)
    await backend.connect()
    queue = TaskQueue(backend)

    # Track concurrent executions
    concurrent_count = 0
    max_observed = 0
    count_lock = asyncio.Lock()
    start_barrier = asyncio.Barrier(5)
    end_barrier = asyncio.Barrier(5)

    async def counting_task(value):
        """Task that tracks concurrent executions."""
        nonlocal concurrent_count, max_observed

        # Increment counter
        async with count_lock:
            concurrent_count += 1
            max_observed = max(max_observed, concurrent_count)
            print(f"  Task {value}: started, concurrent_count={concurrent_count}")

        # Wait for all tasks to start
        await start_barrier.wait()
        print(f"  Task {value}: past start barrier, max_observed={max_observed}")

        # Sleep a bit
        await asyncio.sleep(0.1)

        # Wait for all tasks to be ready to finish
        await end_barrier.wait()

        # Decrement counter
        async with count_lock:
            concurrent_count -= 1
            print(f"  Task {value}: finished, concurrent_count={concurrent_count}")

        return value

    # Enqueue 5 tasks
    print("Enqueueing 5 tasks...")
    task_ids = []
    for i in range(5):
        task_id = await queue.enqueue(counting_task, i)
        task_ids.append(task_id)

    # Create worker with max_concurrency=2
    print("\nStarting worker with max_concurrency=2...")
    worker = Worker(backend, max_concurrency=2, poll_interval=0.01)

    # Start worker in background
    worker_task = asyncio.create_task(worker.start())

    # Wait for tasks to complete
    print("\nWaiting for tasks to complete...")
    results = []
    for task_id in task_ids:
        result = await queue.get_result(task_id, timeout=10.0)
        results.append(result)

    # Stop worker
    print("\nStopping worker...")
    await worker.stop()
    await worker_task

    # Verify results
    print(f"\nResults: {sorted(results)}")
    assert sorted(results) == [0, 1, 2, 3, 4], "Results should contain all values"

    # Verify concurrency was bounded
    print(f"\nMax concurrent executions observed: {max_observed}")
    assert max_observed == 2, f"Expected max_concurrency=2, but observed {max_observed}"

    print("\n✓ Test passed: Worker correctly bounds concurrency!")

    # Cleanup
    await backend.close()
    import os

    os.unlink(db_path)


if __name__ == "__main__":
    asyncio.run(test_concurrency_bounded())
