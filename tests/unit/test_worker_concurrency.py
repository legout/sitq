"""Test bounded worker concurrency."""

import asyncio
import pytest

from sitq import Worker, TaskQueue, SQLiteBackend
from sitq.core import ReservedTask
from datetime import datetime, timezone


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_worker_never_exceeds_max_concurrency():
    """
    Prove worker never executes more than max_concurrency tasks simultaneously.

    Uses a counter and barrier to track concurrent executions and ensure
    the limit is never exceeded.
    """

    # Use an in-memory SQLite database for testing
    backend = SQLiteBackend(":memory:")
    await backend.connect()
    queue = TaskQueue(backend)

    # Track concurrent executions
    concurrent_count = 0
    max_observed = 0
    count_lock = asyncio.Lock()

    # Barrier to synchronize task starts
    # This ensures all tasks start before any complete
    start_barrier = asyncio.Barrier(5)
    end_barrier = asyncio.Barrier(5)

    async def counting_task(value):
        """Task that increments counter and waits on barriers."""
        nonlocal concurrent_count, max_observed

        # Increment counter
        async with count_lock:
            concurrent_count += 1
            max_observed = max(max_observed, concurrent_count)

        # Wait for all tasks to start (ensures we capture max concurrency)
        await start_barrier.wait()

        # Sleep a bit to ensure we maintain concurrent state
        await asyncio.sleep(0.1)

        # Wait for all tasks to be ready to finish
        await end_barrier.wait()

        # Decrement counter
        async with count_lock:
            concurrent_count -= 1

        return value

    # Enqueue 5 tasks
    task_ids = []
    for i in range(5):
        task_id = await queue.enqueue(counting_task, i)
        task_ids.append(task_id)

    # Create worker with max_concurrency=2
    worker = Worker(backend, max_concurrency=2, poll_interval=0.01)

    # Start worker in background
    worker_task = asyncio.create_task(worker.start())

    # Wait for tasks to complete
    results = []
    for task_id in task_ids:
        result = await queue.get_result(task_id, timeout=0.5)
        results.append(result)

    # Stop worker
    await worker.stop()
    await worker_task

    # Verify results
    successful_results = [r for r in results if r is not None]
    assert sorted(successful_results) == [0, 1, 2, 3, 4]

    # Verify concurrency was bounded
    assert max_observed == 2, (
        f"Expected max_concurrency=2, but observed {max_observed} concurrent executions"
    )


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_stop_waits_for_in_flight_tasks():
    """
    Verify that stop() waits for all in-flight tasks to complete.
    """

    backend = SQLiteBackend(":memory:")
    await backend.connect()
    queue = TaskQueue(backend)

    task_started = asyncio.Event()
    task_can_finish = asyncio.Event()

    async def slow_task():
        task_started.set()
        await task_can_finish.wait()
        return "done"

    # Enqueue a slow task
    task_id = await queue.enqueue(slow_task)

    # Start worker
    worker = Worker(backend, max_concurrency=1, poll_interval=0.01)
    worker_task = asyncio.create_task(worker.start())

    # Wait for task to start
    await task_started.wait()

    # Stop worker - should wait for task to complete
    stop_task = asyncio.create_task(worker.stop())

    # Verify stop() hasn't returned yet
    assert not stop_task.done()

    # Allow task to finish
    task_can_finish.set()

    # Now stop() should complete
    await stop_task
    await worker_task

    # Verify task completed successfully
    result = await queue.get_result(task_id)
    assert result == "done"


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_concurrency_with_failures():
    """
    Verify that task failures don't affect concurrency counting
    or crash the worker loop.
    """

    backend = SQLiteBackend(":memory:")
    await backend.connect()
    queue = TaskQueue(backend)

    # Track execution
    execution_count = 0
    failure_count = 0
    success_count = 0
    execution_lock = asyncio.Lock()
    barrier = asyncio.Barrier(5)

    async def failing_task(value):
        nonlocal execution_count, failure_count, success_count

        async with execution_lock:
            execution_count += 1

        await barrier.wait()

        # Every other task fails
        if value % 2 == 0:
            async with execution_lock:
                failure_count += 1
            raise ValueError(f"Task {value} failed")
        else:
            async with execution_lock:
                success_count += 1
            return value

    # Enqueue 5 tasks
    task_ids = []
    for i in range(5):
        task_id = await queue.enqueue(failing_task, i)
        task_ids.append(task_id)

    # Create worker with max_concurrency=3
    worker = Worker(backend, max_concurrency=3, poll_interval=0.01)
    await worker.start()

    # Wait for all results
    results = []
    for task_id in task_ids:
        result = await queue.get_result(task_id, timeout=5.0)
        results.append(result)

    await worker.stop()

    # Verify all 5 tasks were executed
    assert execution_count == 5

    # Verify 2 failed (even values), 3 succeeded (odd values)
    assert failure_count == 2
    assert success_count == 3

    # Verify results (failed tasks should be None)
    expected = [None, 1, None, 3, None]
    assert results == expected
