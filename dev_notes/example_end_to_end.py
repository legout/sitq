"""
Sitq: Simple Task Queue - End-to-End Example

This script demonstrates the complete workflow:
1. Enqueue tasks
2. Worker processes tasks
3. Retrieve results
"""

import asyncio
import tempfile
from sitq import TaskQueue, Worker, SQLiteBackend


async def task_a(name: str, delay: float) -> str:
    """Example async task with delay."""
    print(f"Task {name}: starting...")
    await asyncio.sleep(delay)
    print(f"Task {name}: completed!")
    return f"Result from {name}"


def task_b(name: str) -> str:
    """Example sync task."""
    print(f"Task {name}: starting...")
    # Simulate work
    import time

    time.sleep(0.5)
    print(f"Task {name}: completed!")
    return f"Result from {name}"


async def failing_task():
    """Example task that fails."""
    raise ValueError("This task always fails")


async def main():
    """Run complete end-to-end example."""
    print("=" * 50)
    print("Sitq End-to-End Example")
    print("=" * 50)
    print()

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

        # Setup
        backend = SQLiteBackend(db_path)
        await backend.connect()
        queue = TaskQueue(backend)

        print("✓ Connected to SQLite backend")
        print()

        # Enqueue tasks
        print("Enqueueing tasks...")
        print()

        task1_id = await queue.enqueue(task_a, "AsyncTask1", 1.0)
        print(f"  Task 1 (async): {task1_id}")

        task2_id = await queue.enqueue(task_a, "AsyncTask2", 0.5)
        print(f"  Task 2 (async): {task2_id}")

        task3_id = await queue.enqueue(task_b, "SyncTask")
        print(f"  Task 3 (sync): {task3_id}")

        task4_id = await queue.enqueue(failing_task)
        print(f"  Task 4 (failing): {task4_id}")

        print()
        print("-" * 50)
        print()

        # Start worker
        print("Starting worker with max_concurrency=2...")
        worker = Worker(backend, max_concurrency=2, poll_interval=0.1)
        worker_task = asyncio.create_task(worker.start())
        print("✓ Worker started")
        print()

        # Wait for results
        print("Waiting for results...")
        print("-" * 50)
        print()

        results = []

        # Task 1 (async, 1s delay)
        result = await queue.get_result(task1_id, timeout=5.0)
        if result and result.status == "success":
            value = queue.deserialize_result(result)
            print(f"✓ Task 1 completed: {value}")
            results.append(value)
        elif result and result.status == "failed":
            print(f"✗ Task 1 failed: {result.error}")
        print()

        # Task 2 (async, 0.5s delay)
        result = await queue.get_result(task2_id, timeout=5.0)
        if result and result.status == "success":
            value = queue.deserialize_result(result)
            print(f"✓ Task 2 completed: {value}")
            results.append(value)
        elif result and result.status == "failed":
            print(f"✗ Task 2 failed: {result.error}")
        print()

        # Task 3 (sync, 0.5s work)
        result = await queue.get_result(task3_id, timeout=5.0)
        if result and result.status == "success":
            value = queue.deserialize_result(result)
            print(f"✓ Task 3 completed: {value}")
            results.append(value)
        elif result and result.status == "failed":
            print(f"✗ Task 3 failed: {result.error}")
        print()

        # Task 4 (failing)
        result = await queue.get_result(task4_id, timeout=5.0)
        if result and result.status == "failed":
            print(f"✓ Task 4 failed as expected: {result.error}")
            results.append(None)
        print()

        # Stop worker
        print("Stopping worker...")
        await worker.stop()
        await worker_task
        print("✓ Worker stopped")
        print()

        # Summary
        print("=" * 50)
        print("Summary")
        print("=" * 50)
        print(f"Total tasks enqueued: 4")
        print(f"Successful results: {len([r for r in results if r is not None])}")
        print(f"Failed results: {len([r for r in results if r is None])}")
        print()
        print(f"Results: {results}")
        print()

        # Cleanup
        await backend.close()
        import os

        os.unlink(db_path)


if __name__ == "__main__":
    asyncio.run(main())
