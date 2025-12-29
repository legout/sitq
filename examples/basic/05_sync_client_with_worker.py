#!/usr/bin/env python3
"""Sync client with async worker example.

This example shows:
1. Using SyncTaskQueue for synchronous task enqueuing
2. Running an async worker that processes tasks from the same SQLite DB
3. Coordination between sync producer and async consumer via threading
4. Shared database backend enabling sync/async communication

Run this example:
    python 05_sync_client_with_worker.py
"""

import asyncio
import tempfile
import threading
import time
from pathlib import Path

from sitq import TaskQueue, Worker, SQLiteBackend, SyncTaskQueue


async def async_task(name: str) -> str:
    """Async task that can be executed by the async worker."""
    await asyncio.sleep(0.2)
    return f"Async processed: {name}"


def sync_multiply(a: int, b: int) -> int:
    """Sync task that can be executed by the async worker."""
    return a * b


def run_sync_producer(db_path: str, results: dict):
    """Run sync task producer in a separate thread.

    This demonstrates using SyncTaskQueue in a truly synchronous context.
    """
    backend = SQLiteBackend(db_path)

    print("\n   [Sync Producer] Enqueueing tasks...")

    with SyncTaskQueue(backend) as queue:
        task_id_1 = queue.enqueue(sync_multiply, 5, 3)
        task_id_2 = queue.enqueue(async_task, "Task A")
        task_id_3 = queue.enqueue(async_task, "Task B")
        task_id_4 = queue.enqueue(sync_multiply, 7, 2)

        print(f"   [Sync Producer] Enqueued task 1: {task_id_1}")
        print(f"   [Sync Producer] Enqueued task 2: {task_id_2}")
        print(f"   [Sync Producer] Enqueued task 3: {task_id_3}")
        print(f"   [Sync Producer] Enqueued task 4: {task_id_4}")

        results["enqueued"] = [task_id_1, task_id_2, task_id_3, task_id_4]

    print("   [Sync Producer] Waiting for worker to process...")
    time.sleep(2)

    print("\n   [Sync Producer] Retrieving results...")

    with SyncTaskQueue(backend) as queue:
        for i, task_id in enumerate(results["enqueued"], 1):
            result = queue.get_result(task_id, timeout=5)
            results[f"result_{i}"] = result
            print(f"   [Sync Producer] Task {i} result: {result}")


async def run_async_worker(db_path: str):
    """Run async worker to process tasks from shared DB."""
    backend = SQLiteBackend(db_path)
    worker = Worker(backend)

    print("   [Async Worker] Starting...")
    await worker.start()


def main():
    """Run sync client with async worker example using threading."""

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "tasks.db"

        print("=== sitq Sync Client with Async Worker Example ===\n")

        print("1. Setting up shared backend...")
        print(f"   Backend: {db_path}\n")

        print("2. Starting async worker in background...")

        results = {}

        def worker_thread_func():
            asyncio.run(run_async_worker(str(db_path)))

        worker_thread = threading.Thread(target=worker_thread_func, daemon=True)
        worker_thread.start()
        time.sleep(0.5)
        print("   [Async Worker] Running\n")

        print("3. Running sync producer in separate thread...")

        def producer_thread_func():
            run_sync_producer(str(db_path), results)

        producer_thread = threading.Thread(target=producer_thread_func)
        producer_thread.start()
        producer_thread.join()

        print("\n4. Waiting for async worker to complete processing...")
        time.sleep(1)

        print("\n5. Summary of processed tasks:")
        for i in range(1, 5):
            if f"result_{i}" in results:
                print(f"   Task {i}: {results[f'result_{i}']}")

        print("\n   [Async Worker] Stopping...")

        print("\n=== Example Complete ===")
        print("\nKey Points:")
        print("  - SyncTaskQueue provides blocking interface for sync code")
        print(
            "  - Must run in separate thread from async worker (no event loop conflict)"
        )
        print("  - Async Worker processes tasks from the same SQLite DB")
        print("  - Shared backend enables sync/async communication")
        print("  - Use threading to combine sync and async workflows")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        raise
