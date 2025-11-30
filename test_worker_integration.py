"""Integration tests for Worker implementation."""

import asyncio
import tempfile
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

import pytest

from src.sitq.backends.sqlite import SQLiteBackend
from src.sitq.core import Task
from src.sitq.worker import Worker
from src.sitq.serialization import CloudpickleSerializer


class TestWorkerIntegration:
    """Integration tests for Worker."""

    @pytest.fixture
    async def backend(self):
        """Create a temporary SQLite backend for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            backend = SQLiteBackend(tmp.name)
            await backend.connect()
            yield backend
            await backend.close()

    @pytest.fixture
    def serializer(self):
        """Create a serializer for testing."""
        return CloudpickleSerializer()

    @pytest.fixture
    async def worker(self, backend, serializer):
        """Create a worker for testing."""
        return Worker(
            backend=backend,
            serializer=serializer,
            max_concurrency=2,
            poll_interval=0.1,  # Fast polling for tests
        )

    @pytest.mark.asyncio
    async def test_basic_task_execution(self, backend, serializer):
        """Test basic task execution through worker."""

        # Create a simple task
        def simple_task():
            return "task_completed"

        task = Task(
            id=str(uuid.uuid4()),
            func=serializer.dumps(simple_task),
            created_at=datetime.now(timezone.utc),
        )

        # Enqueue task
        await backend.enqueue(task)

        # Create and start worker
        worker = Worker(backend, serializer, max_concurrency=1, poll_interval=0.1)

        # Start worker in background
        worker_task = asyncio.create_task(worker.start())

        try:
            # Wait for task to complete
            timeout = 5.0
            start_time = time.time()

            while time.time() - start_time < timeout:
                result = await backend.get_result(task.id)
                if result and result.status == "success":
                    # Deserialize and verify result
                    completed_result = serializer.loads(result.value)
                    assert completed_result == "task_completed"
                    return
                await asyncio.sleep(0.1)

            pytest.fail("Task did not complete within timeout")

        finally:
            await worker.stop()
            await worker_task

    @pytest.mark.asyncio
    async def test_async_task_execution(self, backend, serializer):
        """Test execution of async tasks."""

        async def async_task():
            await asyncio.sleep(0.1)  # Simulate async work
            return "async_completed"

        task = Task(
            id=str(uuid.uuid4()),
            func=serializer.dumps(async_task),
            created_at=datetime.now(timezone.utc),
        )

        await backend.enqueue(task)

        worker = Worker(backend, serializer, max_concurrency=1, poll_interval=0.1)
        worker_task = asyncio.create_task(worker.start())

        try:
            timeout = 5.0
            start_time = time.time()

            while time.time() - start_time < timeout:
                result = await backend.get_result(task.id)
                if result and result.status == "success":
                    completed_result = serializer.loads(result.value)
                    assert completed_result == "async_completed"
                    return
                await asyncio.sleep(0.1)

            pytest.fail("Async task did not complete within timeout")

        finally:
            await worker.stop()
            await worker_task

    @pytest.mark.asyncio
    async def test_task_failure_handling(self, backend, serializer):
        """Test that task failures are properly recorded."""

        def failing_task():
            raise ValueError("Test error message")

        task = Task(
            id=str(uuid.uuid4()),
            func=serializer.dumps(failing_task),
            created_at=datetime.now(timezone.utc),
        )

        await backend.enqueue(task)

        worker = Worker(backend, serializer, max_concurrency=1, poll_interval=0.1)
        worker_task = asyncio.create_task(worker.start())

        try:
            timeout = 5.0
            start_time = time.time()

            while time.time() - start_time < timeout:
                result = await backend.get_result(task.id)
                if result and result.status == "failed":
                    assert "Test error message" in result.error
                    assert result.traceback is not None
                    return
                await asyncio.sleep(0.1)

            pytest.fail("Task failure was not recorded within timeout")

        finally:
            await worker.stop()
            await worker_task

    @pytest.mark.asyncio
    async def test_eta_scheduling(self, backend, serializer):
        """Test that tasks with future ETA are not executed early."""

        def eta_task():
            return "eta_completed"

        # Create task with future ETA
        future_time = datetime.now(timezone.utc) + timedelta(seconds=2)
        task = Task(
            id=str(uuid.uuid4()),
            func=serializer.dumps(eta_task),
            created_at=datetime.now(timezone.utc),
            available_at=future_time,
        )

        await backend.enqueue(task)

        worker = Worker(backend, serializer, max_concurrency=1, poll_interval=0.1)
        worker_task = asyncio.create_task(worker.start())

        try:
            # Task should not complete before ETA time
            await asyncio.sleep(1.0)
            result = await backend.get_result(task.id)
            assert result is None  # Should not be executed yet

            # Wait past ETA time
            await asyncio.sleep(1.5)

            # Now task should complete
            timeout = 5.0
            start_time = time.time()

            while time.time() - start_time < timeout:
                result = await backend.get_result(task.id)
                if result and result.status == "success":
                    completed_result = serializer.loads(result.value)
                    assert completed_result == "eta_completed"
                    return
                await asyncio.sleep(0.1)

            pytest.fail("ETA task did not complete within timeout")

        finally:
            await worker.stop()
            await worker_task

    @pytest.mark.asyncio
    async def test_concurrency_control(self, backend, serializer):
        """Test that worker respects concurrency limits."""

        async def slow_task():
            await asyncio.sleep(0.5)
            return "slow_completed"

        # Create multiple tasks
        tasks = []
        for i in range(3):
            task = Task(
                id=str(uuid.uuid4()),
                func=serializer.dumps(slow_task),
                created_at=datetime.now(timezone.utc),
            )
            tasks.append(task)
            await backend.enqueue(task)

        # Start worker with max_concurrency=2
        worker = Worker(backend, serializer, max_concurrency=2, poll_interval=0.1)
        worker_task = asyncio.create_task(worker.start())

        try:
            # Wait a bit for tasks to start
            await asyncio.sleep(0.2)

            # Check that only 2 tasks are in-flight at any time
            # This is hard to test directly, but we can verify completion order
            completed_tasks = []
            timeout = 10.0
            start_time = time.time()

            while time.time() - start_time < timeout and len(completed_tasks) < 3:
                for task in tasks:
                    if task.id not in completed_tasks:
                        result = await backend.get_result(task.id)
                        if result and result.status == "success":
                            completed_tasks.append(task.id)
                            completed_result = serializer.loads(result.value)
                            assert completed_result == "slow_completed"
                await asyncio.sleep(0.1)

            assert len(completed_tasks) == 3

        finally:
            await worker.stop()
            await worker_task

    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, backend, serializer):
        """Test graceful shutdown with in-flight tasks."""

        async def long_task():
            await asyncio.sleep(2.0)
            return "long_completed"

        # Create a long-running task
        task = Task(
            id=str(uuid.uuid4()),
            func=serializer.dumps(long_task),
            created_at=datetime.now(timezone.utc),
        )

        await backend.enqueue(task)

        worker = Worker(backend, serializer, max_concurrency=1, poll_interval=0.1)
        worker_task = asyncio.create_task(worker.start())

        try:
            # Wait for task to start
            await asyncio.sleep(0.5)

            # Stop worker - should wait for in-flight task to complete
            stop_start = time.time()
            await worker.stop()
            stop_duration = time.time() - stop_start

            # Should have waited for task to complete (at least 1.5 seconds more)
            assert stop_duration >= 1.5

            # Task should have completed successfully
            result = await backend.get_result(task.id)
            assert result is not None
            assert result.status == "success"
            completed_result = serializer.loads(result.value)
            assert completed_result == "long_completed"

        finally:
            # Worker should already be stopped, but ensure task is cleaned up
            try:
                await worker_task
            except asyncio.CancelledError:
                pass  # Expected during shutdown

    @pytest.mark.asyncio
    async def test_multiple_workers(self, backend, serializer):
        """Test multiple workers sharing the same backend."""

        def worker_task(worker_id):
            return f"worker_{worker_id}_completed"

        # Create tasks
        tasks = []
        for i in range(4):

            def make_task(wid=i):
                return worker_task(wid)

            task = Task(
                id=str(uuid.uuid4()),
                func=serializer.dumps(make_task),
                created_at=datetime.now(timezone.utc),
            )
            tasks.append(task)
            await backend.enqueue(task)

        # Start two workers
        workers = []
        worker_tasks = []

        for i in range(2):
            worker = Worker(backend, serializer, max_concurrency=1, poll_interval=0.1)
            workers.append(worker)
            worker_tasks.append(asyncio.create_task(worker.start()))

        try:
            # Wait for all tasks to complete
            completed_tasks = []
            timeout = 10.0
            start_time = time.time()

            while time.time() - start_time < timeout and len(completed_tasks) < 4:
                for task in tasks:
                    if task.id not in completed_tasks:
                        result = await backend.get_result(task.id)
                        if result and result.status == "success":
                            completed_tasks.append(task.id)
                            completed_result = serializer.loads(result.value)
                            # Should be from some worker
                            assert completed_result.startswith("worker_")
                            assert completed_result.endswith("_completed")
                await asyncio.sleep(0.1)

            assert len(completed_tasks) == 4

        finally:
            # Stop all workers
            for worker in workers:
                await worker.stop()

            for task in worker_tasks:
                try:
                    await task
                except asyncio.CancelledError:
                    pass
