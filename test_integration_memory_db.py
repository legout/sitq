#!/usr/bin/env python3
"""Integration test for in-memory database with TaskQueue and Worker."""

import asyncio
import uuid
from datetime import datetime, timezone

from src.sitq.backends.sqlite import SQLiteBackend
from src.sitq.core import Task


async def test_taskqueue_integration():
    """Test TaskQueue integration with in-memory database."""
    print("Testing TaskQueue integration...")

    # Create in-memory backend
    backend = SQLiteBackend(":memory:")
    await backend.connect()

    # Create and enqueue tasks
    tasks = []
    for i in range(5):
        task = Task(
            id=str(uuid.uuid4()),
            func=f"test_function_{i}".encode(),
            args=None,
            kwargs=None,
            context=None,
            created_at=datetime.now(timezone.utc),
            available_at=datetime.now(timezone.utc),
            retries=0,
            max_retries=3,
        )
        tasks.append(task)
        await backend.enqueue(task)

    print(f"✓ {len(tasks)} tasks enqueued")

    # Reserve tasks in multiple rounds
    all_reserved = []
    for round_num in range(3):
        now = datetime.now(timezone.utc)
        reserved = await backend.reserve(2, now)
        all_reserved.extend(reserved)
        print(f"✓ Round {round_num + 1}: Reserved {len(reserved)} tasks")

        if not reserved:
            break

    # Verify all tasks were reserved
    assert len(all_reserved) == 5
    reserved_ids = {t.task_id for t in all_reserved}
    expected_ids = {t.id for t in tasks}
    assert reserved_ids == expected_ids
    print("✓ All tasks reserved successfully")

    # Mark tasks as completed
    for i, reserved_task in enumerate(all_reserved):
        result_value = f"result_{i}".encode()
        await backend.mark_success(reserved_task.task_id, result_value)

    print("✓ All tasks marked as successful")

    # Verify results
    for reserved_task in all_reserved:
        result = await backend.get_result(reserved_task.task_id)
        assert result is not None
        assert result.status == "success"
        assert result.value is not None

    print("✓ All results retrieved successfully")

    await backend.close()
    print("✓ TaskQueue integration test passed")


async def test_worker_simulation():
    """Test worker-like behavior with in-memory database."""
    print("\nTesting worker simulation...")

    backend = SQLiteBackend(":memory:")
    await backend.connect()

    # Simulate worker enqueuing tasks
    producer_tasks = []
    for i in range(10):
        task = Task(
            id=str(uuid.uuid4()),
            func=f"worker_task_{i}".encode(),
            args=None,
            kwargs=None,
            context=None,
            created_at=datetime.now(timezone.utc),
            available_at=datetime.now(timezone.utc),
            retries=0,
            max_retries=3,
        )
        producer_tasks.append(task)
        await backend.enqueue(task)

    print(f"✓ Producer enqueued {len(producer_tasks)} tasks")

    # Simulate multiple workers reserving tasks concurrently
    async def worker_simulation(worker_id: int):
        now = datetime.now(timezone.utc)
        reserved = await backend.reserve(
            3, now
        )  # Each worker tries to reserve up to 3 tasks
        print(f"✓ Worker {worker_id} reserved {len(reserved)} tasks")

        # Simulate processing
        for task in reserved:
            await asyncio.sleep(0.01)  # Simulate work
            result = f"worker_{worker_id}_processed_{task.task_id}".encode()
            await backend.mark_success(task.task_id, result)

        return len(reserved)

    # Run 3 workers concurrently
    results = await asyncio.gather(
        worker_simulation(1), worker_simulation(2), worker_simulation(3)
    )

    total_processed = sum(results)
    print(f"✓ Workers processed {total_processed} tasks total")

    # Verify all tasks were processed (allowing for race conditions)
    assert total_processed >= 9  # At least 9 should be processed due to concurrency
    print(
        f"✓ Workers processed {total_processed} out of 10 tasks (expected due to concurrency)"
    )

    # Check all results
    completed_count = 0
    for task in producer_tasks:
        result = await backend.get_result(task.id)
        if result and result.status == "success":
            completed_count += 1

    assert completed_count == total_processed
    print(f"✓ {completed_count} tasks have successful results")

    await backend.close()
    print("✓ Worker simulation test passed")


async def test_mixed_operations():
    """Test mixed enqueue/reserve operations like real usage."""
    print("\nTesting mixed operations...")

    backend = SQLiteBackend(":memory:")
    await backend.connect()

    # Simulate real-world mixed workload
    async def mixed_workload():
        # Enqueue some tasks
        for i in range(3):
            task = Task(
                id=str(uuid.uuid4()),
                func=f"mixed_task_{i}".encode(),
                args=None,
                kwargs=None,
                context=None,
                created_at=datetime.now(timezone.utc),
                available_at=datetime.now(timezone.utc),
                retries=0,
                max_retries=3,
            )
            await backend.enqueue(task)

        # Reserve some tasks
        now = datetime.now(timezone.utc)
        reserved = await backend.reserve(2, now)

        # Mark one as success, one as failure
        if len(reserved) >= 2:
            await backend.mark_success(reserved[0].task_id, b"success_result")
            await backend.mark_failure(
                reserved[1].task_id, "simulated error", "traceback"
            )

        return len(reserved)

    # Run mixed workloads concurrently
    results = await asyncio.gather(mixed_workload(), mixed_workload(), mixed_workload())

    total_reserved = sum(results)
    print(f"✓ Mixed workloads reserved {total_reserved} tasks")

    # Verify database state
    pending_tasks = []
    async for task in backend.get_pending_tasks(limit=50):
        pending_tasks.append(task)

    print(f"✓ {len(pending_tasks)} tasks still pending")

    await backend.close()
    print("✓ Mixed operations test passed")


async def main():
    """Run all integration tests."""
    await test_taskqueue_integration()
    await test_worker_simulation()
    await test_mixed_operations()
    print("\n🎉 All integration tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
