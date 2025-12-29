#!/usr/bin/env python3
"""Bounded concurrency example using max_concurrency parameter.

This example shows:
1. Configuring Worker with max_concurrency limit
2. Observing how bounded concurrency affects task execution timing
3. Verifying that tasks execute in parallel up to the limit
4. Understanding resource management with controlled parallelism

Run this example:
    python 03_bounded_concurrency.py
"""

import asyncio
import tempfile
import time
from pathlib import Path

from sitq import TaskQueue, Worker, SQLiteBackend


execution_times = []


async def slow_task(task_id: int, sleep_time: float = 0.5) -> str:
    """Task that simulates work with a sleep."""
    start_time = time.time()
    await asyncio.sleep(sleep_time)
    end_time = time.time()
    execution_times.append((task_id, start_time, end_time))
    return f"Task {task_id} completed in {end_time - start_time:.2f}s"


def analyze_execution_times():
    """Analyze execution times to verify concurrency behavior."""
    if not execution_times:
        return

    print("\n   Execution Timeline Analysis:")
    print("   " + "-" * 50)

    # Find global start and end
    all_times = [t for times in execution_times for t in times[1:]]
    min_time = min(all_times)
    max_time = max(all_times)

    # Calculate overlaps
    concurrent_counts = []
    for task_id, start, end in execution_times:
        concurrent_at_start = sum(
            1
            for _, t_start, t_end in execution_times
            if t_start <= start <= t_end and task_id != _
        )
        concurrent_counts.append(concurrent_at_start + 1)

        print(
            f"   Task {task_id}: start={start - min_time:.2f}s, end={end - min_time:.2f}s"
        )

    max_concurrent = max(concurrent_counts) if concurrent_counts else 0
    print("   " + "-" * 50)
    print(f"   Max concurrent tasks: {max_concurrent}")
    print(f"   Total elapsed time: {max_time - min_time:.2f}s")


async def main():
    """Run the bounded concurrency example."""

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "tasks.db"

        print("=== sitq Bounded Concurrency Example ===\n")

        print("1. Setting up backend and task queue...")
        backend = SQLiteBackend(str(db_path))
        queue = TaskQueue(backend=backend)

        async with queue:
            print(f"   Backend: {db_path}")
            print("   Queue connected\n")

            print("2. Enqueuing 5 tasks (each takes ~0.5s)...")
            task_ids = []
            for i in range(1, 6):
                task_id = await queue.enqueue(slow_task, i, 0.5)
                task_ids.append(task_id)
                print(f"   Enqueued task {i}: {task_id}")

            print("\n   Without concurrency limits:")
            print("   - All 5 tasks would complete in ~0.5s (perfectly parallel)")
            print("   - With max_concurrency=2, expect ~1.25s (2 + 2 + 1)\n")

            print("3. Starting worker with max_concurrency=2...")
            worker = Worker(backend, max_concurrency=2, poll_interval=0.2)

            start_time = time.time()
            worker_task = asyncio.create_task(worker.start())

            await asyncio.sleep(4)

            print("   Worker stopped\n")

            print("4. Retrieving results...")
            for i, task_id in enumerate(task_ids, 1):
                result = await queue.get_result(task_id)
                if result and result.status == "success":
                    value = queue.deserialize_result(result)
                    print(f"   {value}")

            await worker.stop()

            end_time = time.time()
            print(f"\n5. Total execution time: {end_time - start_time:.2f}s")

            analyze_execution_times()

            print("\n=== Example Complete ===")
            print("\nKey Points:")
            print(
                "  - Worker with max_concurrency=2 executes at most 2 tasks simultaneously"
            )
            print("  - Tasks wait in queue when concurrency limit is reached")
            print("  - Bounded concurrency prevents resource exhaustion")
            print("  - Adjust max_concurrency based on your task characteristics")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        raise
