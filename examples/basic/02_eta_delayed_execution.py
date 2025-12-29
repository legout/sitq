#!/usr/bin/env python3
"""Delayed execution example using the eta parameter.

This example shows:
1. Enqueuing tasks with scheduled execution times (eta)
2. Using timezone-aware UTC datetimes
3. Observing that tasks execute only after their eta
4. Retrieving results from delayed tasks

Run this example:
    python 02_eta_delayed_execution.py
"""

import asyncio
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

from sitq import TaskQueue, Worker, SQLiteBackend


async def delayed_task(message: str) -> str:
    """Task that executes after a delay."""
    return f"Executed at: {datetime.now(timezone.utc).isoformat()} | {message}"


async def main():
    """Run the delayed execution example."""

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "tasks.db"

        print("=== sitq Delayed Execution (ETA) Example ===\n")

        print("1. Setting up backend and task queue...")
        backend = SQLiteBackend(str(db_path))
        queue = TaskQueue(backend=backend)

        async with queue:
            print(f"   Backend: {db_path}")
            print("   Queue connected\n")

            print("2. Enqueuing tasks with different ETAs...")
            now = datetime.now(timezone.utc)

            eta_1 = now + timedelta(seconds=1)
            task_id_1 = await queue.enqueue(
                delayed_task, "Task 1 (1 second delay)", eta=eta_1
            )
            print(f"   Task 1 scheduled at: {eta_1.isoformat()}")

            eta_2 = now + timedelta(seconds=2)
            task_id_2 = await queue.enqueue(
                delayed_task, "Task 2 (2 second delay)", eta=eta_2
            )
            print(f"   Task 2 scheduled at: {eta_2.isoformat()}")

            eta_3 = now + timedelta(seconds=3)
            task_id_3 = await queue.enqueue(
                delayed_task, "Task 3 (3 second delay)", eta=eta_3
            )
            print(f"   Task 3 scheduled at: {eta_3.isoformat()}")

            print(f"\n   Current time: {now.isoformat()}")
            print("   Note: UTC timezone required\n")

            print("3. Starting worker...")
            worker = Worker(backend, poll_interval=0.5)

            async def run_worker():
                await worker.start()

            worker_task = asyncio.create_task(run_worker())

            print("   Worker is polling for eligible tasks...")
            print("   Waiting for tasks to become eligible...\n")

            await asyncio.sleep(4)

            print("4. Retrieving results...")

            result_1 = await queue.get_result(task_id_1)
            if result_1 and result_1.status == "success":
                value_1 = queue.deserialize_result(result_1)
                print(f"   Task 1 result: {value_1}")
            else:
                print(
                    f"   Task 1 incomplete: {result_1.status if result_1 else 'not found'}"
                )

            result_2 = await queue.get_result(task_id_2)
            if result_2 and result_2.status == "success":
                value_2 = queue.deserialize_result(result_2)
                print(f"   Task 2 result: {value_2}")
            else:
                print(
                    f"   Task 2 incomplete: {result_2.status if result_2 else 'not found'}"
                )

            result_3 = await queue.get_result(task_id_3)
            if result_3 and result_3.status == "success":
                value_3 = queue.deserialize_result(result_3)
                print(f"   Task 3 result: {value_3}")
            else:
                print(
                    f"   Task 3 incomplete: {result_3.status if result_3 else 'not found'}"
                )

            print("\n5. Stopping worker...")
            await worker.stop()
            print("   Worker stopped\n")

            print("=== Example Complete ===")
            print("\nKey Points:")
            print("  - Tasks are enqueued with eta (estimated time of arrival)")
            print("  - Worker only executes tasks when current time >= eta")
            print("  - ETA must be timezone-aware (UTC recommended)")
            print("  - Tasks are polled and processed in order of eligibility")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        raise
