#!/usr/bin/env python3
"""Simple test script for in-memory database functionality."""

import asyncio
import uuid
from datetime import datetime, timezone

from src.sitq.backends.sqlite import SQLiteBackend
from src.sitq.core import Task


async def test_memory_db():
    """Test basic in-memory database functionality."""
    print("Testing in-memory database...")

    # Create backend
    backend = SQLiteBackend(":memory:")
    await backend.initialize()

    # Create a task
    task = Task(
        id=str(uuid.uuid4()),
        func=b"test_function",  # Serialized function
        args=None,
        kwargs=None,
        context=None,
        created_at=datetime.now(timezone.utc),
        available_at=datetime.now(timezone.utc),
        retries=0,
        max_retries=3,
    )

    # Enqueue task
    await backend.enqueue(task)
    print("✓ Task enqueued")

    # Reserve task
    now = datetime.now(timezone.utc)
    reserved_tasks = await backend.reserve(1, now)
    assert len(reserved_tasks) == 1
    assert reserved_tasks[0].task_id == task.id
    print("✓ Task reserved")

    # Mark as successful
    result_value = b"test_result"
    await backend.mark_success(task.id, result_value)
    print("✓ Task marked as successful")

    # Get result
    result = await backend.get_result(task.id)
    assert result is not None
    assert result.value == result_value
    print("✓ Result retrieved")

    # Close connection
    await backend.close()
    print("✓ Connection closed")

    print("All tests passed! In-memory database is working correctly.")


async def test_concurrent_operations():
    """Test concurrent operations with shared connection."""
    print("\nTesting concurrent operations...")

    backend = SQLiteBackend(":memory:")
    await backend.initialize()

    # Create multiple tasks
    tasks = []
    for i in range(10):
        task = Task(
            id=str(uuid.uuid4()),
            func=f"test_function_{i}".encode(),  # Serialized function
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

    # Concurrent reservations
    now = datetime.now(timezone.utc)
    results = await asyncio.gather(*[backend.reserve(2, now) for _ in range(5)])

    # Should have reserved all tasks without duplication
    total_reserved = sum(len(reserved) for reserved in results)
    assert total_reserved == 10

    # Check for uniqueness
    all_task_ids = []
    for batch in results:
        for task in batch:
            all_task_ids.append(task.task_id)
    assert len(set(all_task_ids)) == 10

    print(f"✓ {total_reserved} tasks reserved concurrently without duplication")

    await backend.close()
    print("✓ Concurrent operations test passed")


async def main():
    """Run all tests."""
    await test_memory_db()
    await test_concurrent_operations()
    print("\n🎉 All in-memory database tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
