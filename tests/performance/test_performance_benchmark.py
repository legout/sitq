#!/usr/bin/env python3
"""Performance benchmark for in-memory database."""

import asyncio
import time
import uuid
from datetime import datetime, timezone

from src.sitq.backends.sqlite import SQLiteBackend
from src.sitq.core import Task


async def benchmark_basic_operations():
    """Benchmark basic enqueue/reserve/complete operations."""
    print("Running performance benchmark...")

    # Test in-memory database
    memory_backend = SQLiteBackend(":memory:")
    await memory_backend.connect()

    num_tasks = 100

    # Benchmark enqueue operations
    start_time = time.time()
    tasks = []
    for i in range(num_tasks):
        task = Task(
            id=str(uuid.uuid4()),
            func=f"benchmark_task_{i}".encode(),
            args=None,
            kwargs=None,
            context=None,
            created_at=datetime.now(timezone.utc),
            available_at=datetime.now(timezone.utc),
            retries=0,
            max_retries=3,
        )
        tasks.append(task)
        await memory_backend.enqueue(task)

    enqueue_time = time.time() - start_time
    print(
        f"✓ Enqueued {num_tasks} tasks in {enqueue_time:.3f}s ({num_tasks / enqueue_time:.0f} tasks/sec)"
    )

    # Benchmark reserve operations
    start_time = time.time()
    total_reserved = 0
    batch_size = 10

    while total_reserved < num_tasks:
        now = datetime.now(timezone.utc)
        reserved = await memory_backend.reserve(batch_size, now)
        total_reserved += len(reserved)

        # Mark as completed to free up for next batch
        for reserved_task in reserved:
            await memory_backend.mark_success(
                reserved_task.task_id, f"result_{reserved_task.task_id}".encode()
            )

    reserve_time = time.time() - start_time
    print(
        f"✓ Reserved and completed {num_tasks} tasks in {reserve_time:.3f}s ({num_tasks / reserve_time:.0f} tasks/sec)"
    )

    await memory_backend.close()

    # Test file database for comparison
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        file_backend = SQLiteBackend(tmp.name)
        await file_backend.connect()

        # Benchmark enqueue (smaller sample for file DB)
        file_num_tasks = 50
        start_time = time.time()

        for i in range(file_num_tasks):
            task = Task(
                id=str(uuid.uuid4()),
                func=f"file_task_{i}".encode(),
                args=None,
                kwargs=None,
                context=None,
                created_at=datetime.now(timezone.utc),
                available_at=datetime.now(timezone.utc),
                retries=0,
                max_retries=3,
            )
            await file_backend.enqueue(task)

        file_enqueue_time = time.time() - start_time
        print(
            f"✓ File DB: Enqueued {file_num_tasks} tasks in {file_enqueue_time:.3f}s ({file_num_tasks / file_enqueue_time:.0f} tasks/sec)"
        )

        # Benchmark reserve
        start_time = time.time()
        total_reserved = 0

        while total_reserved < file_num_tasks:
            now = datetime.now(timezone.utc)
            reserved = await file_backend.reserve(10, now)
            total_reserved += len(reserved)

            for reserved_task in reserved:
                await file_backend.mark_success(
                    reserved_task.task_id, f"result_{reserved_task.task_id}".encode()
                )

        file_reserve_time = time.time() - start_time
        print(
            f"✓ File DB: Reserved and completed {file_num_tasks} tasks in {file_reserve_time:.3f}s ({file_num_tasks / file_reserve_time:.0f} tasks/sec)"
        )

        await file_backend.close()

    # Performance comparison
    print(f"\n📊 Performance Summary:")
    print(f"Memory DB - Enqueue: {num_tasks / enqueue_time:.0f} tasks/sec")
    print(f"Memory DB - Reserve:  {num_tasks / reserve_time:.0f} tasks/sec")
    print(f"File DB   - Enqueue: {file_num_tasks / file_enqueue_time:.0f} tasks/sec")
    print(f"File DB   - Reserve:  {file_num_tasks / file_reserve_time:.0f} tasks/sec")

    # Memory DB should be significantly faster
    if enqueue_time < file_enqueue_time * 0.5:
        print("✅ Memory DB enqueue performance is significantly better than file DB")
    else:
        print("⚠️  Memory DB enqueue performance could be improved")

    if reserve_time < file_reserve_time * 0.5:
        print("✅ Memory DB reserve performance is significantly better than file DB")
    else:
        print("⚠️  Memory DB reserve performance could be improved")


async def benchmark_concurrent_operations():
    """Benchmark concurrent operations."""
    print("\nBenchmarking concurrent operations...")

    backend = SQLiteBackend(":memory:")
    await backend.connect()

    # Enqueue tasks
    num_tasks = 50
    tasks = []
    for i in range(num_tasks):
        task = Task(
            id=str(uuid.uuid4()),
            func=f"concurrent_task_{i}".encode(),
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

    # Benchmark concurrent reservations
    async def worker_benchmark(worker_id: int):
        start_time = time.time()
        now = datetime.now(timezone.utc)
        reserved = await backend.reserve(10, now)

        for reserved_task in reserved:
            await backend.mark_success(
                reserved_task.task_id, f"worker_{worker_id}_result".encode()
            )

        end_time = time.time()
        return len(reserved), end_time - start_time

    # Run 5 workers concurrently
    start_time = time.time()
    results = await asyncio.gather(
        worker_benchmark(1),
        worker_benchmark(2),
        worker_benchmark(3),
        worker_benchmark(4),
        worker_benchmark(5),
    )

    total_time = time.time() - start_time
    total_processed = sum(result[0] for result in results)

    print(
        f"✓ 5 workers processed {total_processed} tasks concurrently in {total_time:.3f}s"
    )
    print(f"✓ Concurrent throughput: {total_processed / total_time:.0f} tasks/sec")

    await backend.close()


async def main():
    """Run all benchmarks."""
    await benchmark_basic_operations()
    await benchmark_concurrent_operations()
    print("\n🎉 Performance benchmarking completed!")


if __name__ == "__main__":
    asyncio.run(main())
