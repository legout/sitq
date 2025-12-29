#!/usr/bin/env python3
"""Failure handling and tracebacks example.

This example shows:
1. How task failures are captured and recorded
2. Accessing error messages and tracebacks from failed tasks
3. Understanding Result.status values (success/failed)
4. Proper error handling in task-based workflows

Run this example:
    python 04_failures_and_tracebacks.py
"""

import asyncio
import tempfile
from pathlib import Path

from sitq import TaskQueue, Worker, SQLiteBackend


async def successful_task(name: str) -> str:
    """Task that completes successfully."""
    return f"Hello, {name}!"


async def failing_task_divide_by_zero() -> float:
    """Task that raises a division by zero error."""
    return 1 / 0


async def failing_task_value_error() -> str:
    """Task that raises a ValueError."""
    raise ValueError("Something went wrong!")


async def failing_task_with_context(item: str) -> str:
    """Task that fails with context."""
    if item == "invalid":
        raise KeyError(f"Invalid item: {item}")
    return f"Processed: {item}"


async def main():
    """Run the failure handling example."""

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "tasks.db"

        print("=== sitq Failure Handling and Tracebacks Example ===\n")

        print("1. Setting up backend and task queue...")
        backend = SQLiteBackend(str(db_path))
        queue = TaskQueue(backend=backend)

        async with queue:
            print(f"   Backend: {db_path}")
            print("   Queue connected\n")

            print("2. Enqueuing tasks (some will fail)...")
            task_success = await queue.enqueue(successful_task, "World")
            print(f"   ✓ Success task: {task_success}")

            task_fail_1 = await queue.enqueue(failing_task_divide_by_zero)
            print(f"   ✗ Failing task (divide by zero): {task_fail_1}")

            task_fail_2 = await queue.enqueue(failing_task_value_error)
            print(f"   ✗ Failing task (ValueError): {task_fail_2}")

            task_fail_3 = await queue.enqueue(failing_task_with_context, "invalid")
            print(f"   ✗ Failing task (KeyError): {task_fail_3}")

            print("\n3. Starting worker to process tasks...")
            worker = Worker(backend)

            async def run_worker():
                await worker.start()

            worker_task = asyncio.create_task(run_worker())

            await asyncio.sleep(2)

            print("   Worker processing complete\n")

            print("4. Examining results...\n")

            print("   --- Successful Task ---")
            result = await queue.get_result(task_success)
            if result:
                print(f"   Status: {result.status}")
                if result.status == "success":
                    value = queue.deserialize_result(result)
                    print(f"   Result: {value}")
                else:
                    print(f"   Error: {result.error}")

            print("\n   --- Failing Task (Division by Zero) ---")
            result = await queue.get_result(task_fail_1)
            if result:
                print(f"   Status: {result.status}")
                if result.status == "failed":
                    print(f"   Error: {result.error}")
                    print(f"   Traceback (last 3 lines):")
                    traceback_lines = (
                        result.traceback.split("\n") if result.traceback else []
                    )
                    for line in traceback_lines[-3:]:
                        if line.strip():
                            print(f"   {line}")

            print("\n   --- Failing Task (ValueError) ---")
            result = await queue.get_result(task_fail_2)
            if result:
                print(f"   Status: {result.status}")
                if result.status == "failed":
                    print(f"   Error: {result.error}")

            print("\n   --- Failing Task (KeyError with Context) ---")
            result = await queue.get_result(task_fail_3)
            if result:
                print(f"   Status: {result.status}")
                if result.status == "failed":
                    print(f"   Error: {result.error}")

            print("\n5. Stopping worker...")
            await worker.stop()
            print("   Worker stopped\n")

            print("=== Example Complete ===")
            print("\nKey Points:")
            print("  - Task failures are captured and stored in the Result object")
            print("  - Result.status indicates 'success' or 'failed'")
            print("  - Failed tasks include error message and full traceback")
            print("  - Workers continue processing other tasks after failures")
            print("  - Check result.status before calling deserialize_result()")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        raise
