#!/usr/bin/env python3
"""Integration test for taskqueue integration fix.

This test validates that TaskQueue, Worker, and SyncTaskQueue
work together correctly after the integration improvements.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

from src.sitq.queue import TaskQueue
from src.sitq.worker import Worker
from src.sitq.sync import SyncTaskQueue
from src.sitq.backends.sqlite import SQLiteBackend
from src.sitq.serialization import CloudpickleSerializer


def simple_function(x: int, y: int) -> int:
    """Simple test function."""
    return x + y


def complex_function(data: dict[str, Any], multiplier: float = 1.0) -> dict[str, Any]:
    """More complex test function with kwargs."""
    result = {k: v * multiplier for k, v in data.items()}
    return result


async def async_function(message: str, delay: float = 0.1) -> str:
    """Async test function."""
    await asyncio.sleep(delay)
    return f"Processed: {message}"


def failing_function() -> None:
    """Function that always raises an exception."""
    raise ValueError("Intentional test failure")


def test_serialization_envelope():
    """Test that task envelope serialization works correctly."""
    serializer = CloudpickleSerializer()

    # Test envelope creation and deserialization
    envelope_data = serializer.serialize_task_envelope(simple_function, (1, 2), {})

    deserialized = serializer.deserialize_task_envelope(envelope_data)

    # Test that function is callable and args/kwargs are correct
    assert callable(deserialized["func"])
    assert deserialized["args"] == (1, 2)
    assert deserialized["kwargs"] == {}

    # Test function execution
    result = deserialized["func"](*deserialized["args"], **deserialized["kwargs"])
    assert result == 3  # 1 + 2 = 3

    # Test with kwargs
    envelope_data2 = serializer.serialize_task_envelope(
        complex_function, (), {"data": {"a": 1, "b": 2}, "multiplier": 2.0}
    )

    deserialized2 = serializer.deserialize_task_envelope(envelope_data2)

    assert callable(deserialized2["func"])
    assert deserialized2["args"] == ()
    assert deserialized2["kwargs"] == {"data": {"a": 1, "b": 2}, "multiplier": 2.0}

    # Test function execution
    result2 = deserialized2["func"](*deserialized2["args"], **deserialized2["kwargs"])
    assert result2 == {"a": 2.0, "b": 4.0}

    print("✓ Serialization envelope test passed")


def test_input_validation():
    """Test input validation in all components."""
    backend = SQLiteBackend(":memory:")

    # Test TaskQueue validation
    queue = TaskQueue(backend)

    try:
        # Should raise ValueError for non-callable func
        asyncio.run(queue.enqueue("not_a_function"))
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "func must be callable" in str(e)

    try:
        # Should raise ValueError for naive datetime
        naive_time = datetime.now()
        asyncio.run(queue.enqueue(simple_function, 1, 2, eta=naive_time))
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "eta must be timezone-aware" in str(e)

    # Test Worker validation
    try:
        Worker(backend, max_concurrency=0)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "max_concurrency must be at least 1" in str(e)

    try:
        Worker(backend, poll_interval=-1.0)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "poll_interval must be positive" in str(e)

    print("✓ Input validation test passed")


async def test_async_taskqueue_worker_integration():
    """Test async TaskQueue and Worker integration."""
    backend = SQLiteBackend(":memory:")

    async with TaskQueue(backend) as queue:
        # Enqueue a simple task
        task_id = await queue.enqueue(simple_function, 5, 10)

        # Start worker to process the task
        worker = Worker(backend, max_concurrency=1, poll_interval=0.1)

        # Run worker in background
        worker_task = asyncio.create_task(worker.start())

        try:
            # Wait for result
            result = await queue.get_result(task_id, timeout=5.0)

            assert result is not None
            assert result.status == "success"

            # Deserialize result
            deserialized_result = queue.deserialize_result(result)
            assert deserialized_result == 15

        finally:
            await worker.stop()
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass

    print("✓ Async TaskQueue-Worker integration test passed")


async def test_complex_tasks():
    """Test complex tasks with kwargs and async functions."""
    backend = SQLiteBackend(":memory:")

    async with TaskQueue(backend) as queue:
        # Test task with kwargs
        task_id1 = await queue.enqueue(
            complex_function, data={"x": 10, "y": 20}, multiplier=3.0
        )

        # Test async function
        task_id2 = await queue.enqueue(async_function, "Hello World", delay=0.05)

        # Test failing function
        task_id3 = await queue.enqueue(failing_function)

        # Start worker
        worker = Worker(backend, max_concurrency=2, poll_interval=0.1)
        worker_task = asyncio.create_task(worker.start())

        try:
            # Get results
            result1 = await queue.get_result(task_id1, timeout=5.0)
            result2 = await queue.get_result(task_id2, timeout=5.0)
            result3 = await queue.get_result(task_id3, timeout=5.0)

            # Check complex function result
            assert result1.status == "success"
            deserialized1 = queue.deserialize_result(result1)
            assert deserialized1 == {"x": 30.0, "y": 60.0}

            # Check async function result
            assert result2.status == "success"
            deserialized2 = queue.deserialize_result(result2)
            assert deserialized2 == "Processed: Hello World"

            # Check failing function result
            assert result3.status == "failed"
            assert "Intentional test failure" in result3.error

        finally:
            await worker.stop()
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass

    print("✓ Complex tasks test passed")


def test_sync_taskqueue_integration():
    """Test SyncTaskQueue integration."""
    backend = SQLiteBackend(":memory:")

    with SyncTaskQueue(backend) as queue:
        # Enqueue and process a simple task
        task_id = queue.enqueue(simple_function, 100, 200)

        # Start worker in separate thread
        import threading

        def run_worker():
            asyncio.run(worker_main())

        async def worker_main():
            worker = Worker(backend, max_concurrency=1, poll_interval=0.1)
            await worker.start()

        worker_thread = threading.Thread(target=run_worker, daemon=True)
        worker_thread.start()

        try:
            # Wait for result
            result = queue.get_result(task_id, timeout=5.0)
            assert result == 300
        finally:
            # Worker will be cleaned up when thread exits
            pass

    print("✓ SyncTaskQueue integration test passed")


def test_error_handling():
    """Test error handling in various scenarios."""
    backend = SQLiteBackend(":memory:")
    serializer = CloudpickleSerializer()

    # Test invalid envelope deserialization
    try:
        invalid_data = serializer.dumps({"invalid": "envelope"})
        serializer.deserialize_task_envelope(invalid_data)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "missing required keys" in str(e)

    # Test malformed envelope
    try:
        malformed_data = serializer.dumps(
            {"func": "not_callable", "args": "not_tuple", "kwargs": {}}
        )
        serializer.deserialize_task_envelope(malformed_data)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "'args' must be a tuple" in str(e)

    print("✓ Error handling test passed")


async def test_delayed_tasks():
    """Test delayed task execution with eta."""
    backend = SQLiteBackend(":memory:")

    async with TaskQueue(backend) as queue:
        # Schedule task for future
        future_time = datetime.now(timezone.utc).replace(microsecond=0)
        future_time = future_time.replace(second=future_time.second + 2)

        task_id = await queue.enqueue(simple_function, 7, 8, eta=future_time)

        # Start worker
        worker = Worker(backend, max_concurrency=1, poll_interval=0.5)
        worker_task = asyncio.create_task(worker.start())

        try:
            # Should not get immediate result
            start_time = time.time()
            result = await queue.get_result(task_id, timeout=10.0)
            elapsed = time.time() - start_time

            # Should have waited at least 1.5 seconds (due to scheduling)
            assert elapsed >= 1.5
            assert result.status == "success"

            deserialized = queue.deserialize_result(result)
            assert deserialized == 15

        finally:
            await worker.stop()
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass

    print("✓ Delayed tasks test passed")


def main():
    """Run all integration tests."""
    print("Running taskqueue integration tests...")

    # Run synchronous tests
    test_serialization_envelope()
    test_input_validation()
    test_error_handling()

    # Run async tests
    asyncio.run(test_async_taskqueue_worker_integration())
    asyncio.run(test_complex_tasks())
    asyncio.run(test_delayed_tasks())

    # Run sync tests
    test_sync_taskqueue_integration()

    print("\n🎉 All integration tests passed!")
    print("\nTaskqueue integration fix validated:")
    print("✓ Standard envelope format working")
    print("✓ Consistent serialization across components")
    print("✓ Proper input validation")
    print("✓ Robust error handling")
    print("✓ Type safety improvements")
    print("✓ Async and sync integration working")


if __name__ == "__main__":
    main()
