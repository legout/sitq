#!/usr/bin/env python3
"""End-to-end example demonstrating the complete sitq workflow.

This example shows:
1. Setting up a TaskQueue with a SQLite backend
2. Enqueuing tasks (both async and sync functions)
3. Starting a Worker to process tasks
4. Retrieving and deserializing results
5. Clean shutdown

Run this example:
    python 01_end_to_end.py
"""

import asyncio
import tempfile
from pathlib import Path

from sitq import TaskQueue, Worker, SQLiteBackend


async def say_hello(name: str) -> str:
    """Async task function."""
    await asyncio.sleep(0.1)
    return f"Hello, {name}!"


def add_numbers(a: int, b: int) -> int:
    """Sync task function."""
    return a + b


async def main():
    """Run the end-to-end example."""

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "tasks.db"

        print("=== sitq End-to-End Example ===\n")

        print("1. Setting up backend and task queue...")
        backend = SQLiteBackend(str(db_path))
        queue = TaskQueue(backend=backend)

        async with queue:
            print(f"   Backend: {db_path}")
            print("   Queue connected\n")

            print("2. Enqueuing tasks...")
            task_id_1 = await queue.enqueue(say_hello, "World")
            print(f"   Enqueued async task: {task_id_1}")

            task_id_2 = await queue.enqueue(add_numbers, 5, 3)
            print(f"   Enqueued sync task: {task_id_2}\n")

            print("3. Starting worker...")
            worker = Worker(backend)

            async def run_worker():
                await worker.start()

            worker_task = asyncio.create_task(run_worker())

            await asyncio.sleep(1)

            print("   Worker processing tasks...\n")

            print("4. Retrieving results...")

            result_1 = await queue.get_result(task_id_1)
            if result_1 and result_1.status == "success":
                value_1 = queue.deserialize_result(result_1)
                print(f"   Task {task_id_1}: {value_1}")
            else:
                print(f"   Task {task_id_1} failed or incomplete")

            result_2 = await queue.get_result(task_id_2)
            if result_2 and result_2.status == "success":
                value_2 = queue.deserialize_result(result_2)
                print(f"   Task {task_id_2}: {value_2}")
            else:
                print(f"   Task {task_id_2} failed or incomplete")

            print("\n5. Stopping worker...")
            await worker.stop()
            print("   Worker stopped\n")

            print("=== Example Complete ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        raise
