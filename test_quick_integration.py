#!/usr/bin/env python3
"""Quick integration validation for core in-memory database functionality."""

import asyncio
import uuid
from datetime import datetime, timezone

from src.sitq.backends.sqlite import SQLiteBackend
from src.sitq.core import Task


async def quick_integration_test():
    """Quick test of core integration scenarios."""
    print("Running quick integration validation...")

    backend = SQLiteBackend(":memory:")
    await backend.connect()

    # Test 1: Basic enqueue/reserve/complete cycle
    task = Task(
        id=str(uuid.uuid4()),
        func=b"integration_test",
        args=None,
        kwargs=None,
        context=None,
        created_at=datetime.now(timezone.utc),
        available_at=datetime.now(timezone.utc),
        retries=0,
        max_retries=3,
    )

    await backend.enqueue(task)
    print("✓ Task enqueued")

    reserved = await backend.reserve(1, datetime.now(timezone.utc))
    assert len(reserved) == 1
    assert reserved[0].task_id == task.id
    print("✓ Task reserved")

    await backend.mark_success(task.id, b"integration_result")
    result = await backend.get_result(task.id)
    assert result is not None
    assert result.status == "success"
    print("✓ Task completed and result retrieved")

    # Test 2: Multiple concurrent operations
    tasks = []
    for i in range(5):
        task = Task(
            id=str(uuid.uuid4()),
            func=f"concurrent_test_{i}".encode(),
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

    print("✓ Multiple tasks enqueued")

    # Concurrent reservation
    now = datetime.now(timezone.utc)
    batch1, batch2 = await asyncio.gather(
        backend.reserve(3, now), backend.reserve(3, now)
    )

    total_reserved = len(batch1) + len(batch2)
    assert total_reserved == 5
    print(f"✓ {total_reserved} tasks reserved concurrently without duplication")

    # Mark all as successful
    for batch in [batch1, batch2]:
        for reserved_task in batch:
            await backend.mark_success(reserved_task.task_id, b"concurrent_result")

    print("✓ All concurrent tasks marked successful")

    await backend.close()
    print("✓ Connection closed properly")

    print("\n🎉 Core integration validation passed!")
    print("✓ In-memory database works with TaskQueue-like patterns")
    print("✓ Concurrent operations are handled correctly")
    print("✓ Connection sharing prevents 'no such table' errors")
    print("✓ Atomic task reservation works as expected")


if __name__ == "__main__":
    asyncio.run(quick_integration_test())
