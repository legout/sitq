"""Tests for TaskQueue and Worker serializer integration."""

import pytest
from src.sitq.queue import TaskQueue
from src.sitq.worker import Worker
from src.sitq.serialization import CloudpickleSerializer, Serializer


def test_taskqueue_default_serializer():
    """Test that TaskQueue uses CloudpickleSerializer by default."""
    from src.sitq.backends.base import Backend

    class MockBackend(Backend):
        async def connect(self):
            pass

        async def close(self):
            pass

        async def enqueue(self, task):
            pass

        async def fetch_due_tasks(self, limit=1):
            return []

        async def update_task_state(self, task_id, **kwargs):
            pass

        async def store_result(self, result):
            pass

        async def get_result(self, task_id):
            return None

        async def claim_task(self, task_id, lock_timeout=30):
            return True

        async def release_task(self, task_id):
            pass

        async def schedule_retry(self, task_id, delay):
            pass

    queue = TaskQueue(backend=MockBackend())
    assert isinstance(queue.serializer, CloudpickleSerializer)


def test_taskqueue_custom_serializer():
    """Test that TaskQueue accepts custom serializer."""
    from src.sitq.backends.base import Backend

    class MockBackend(Backend):
        async def connect(self):
            pass

        async def close(self):
            pass

        async def enqueue(self, task):
            pass

        async def fetch_due_tasks(self, limit=1):
            return []

        async def update_task_state(self, task_id, **kwargs):
            pass

        async def store_result(self, result):
            pass

        async def get_result(self, task_id):
            return None

        async def claim_task(self, task_id, lock_timeout=30):
            return True

        async def release_task(self, task_id):
            pass

        async def schedule_retry(self, task_id, delay):
            pass

    custom_serializer = CloudpickleSerializer()
    queue = TaskQueue(backend=MockBackend(), serializer=custom_serializer)
    assert queue.serializer is custom_serializer


def test_worker_default_serializer():
    """Test that Worker uses CloudpickleSerializer by default."""
    worker = Worker()
    assert isinstance(worker.serializer, CloudpickleSerializer)


def test_worker_custom_serializer():
    """Test that Worker accepts custom serializer."""
    custom_serializer = CloudpickleSerializer()
    worker = Worker(serializer=custom_serializer)
    assert worker.serializer is custom_serializer


def test_taskqueue_serializer_round_trip():
    """Test that TaskQueue can properly serialize and deserialize task payloads."""
    from src.sitq.backends.base import Backend

    class MockBackend(Backend):
        async def connect(self):
            pass

        async def close(self):
            pass

        async def enqueue(self, task):
            pass

        async def fetch_due_tasks(self, limit=1):
            return []

        async def update_task_state(self, task_id, **kwargs):
            pass

        async def store_result(self, result):
            pass

        async def get_result(self, task_id):
            return None

        async def claim_task(self, task_id, lock_timeout=30):
            return True

        async def release_task(self, task_id):
            pass

        async def schedule_retry(self, task_id, delay):
            pass

    queue = TaskQueue(backend=MockBackend())

    def example_func(name, count=1):
        return f"Hello {name}! Count: {count}"

    # Create a task payload as it would be created in enqueue
    envelope = {"func": example_func, "args": ("Alice",), "kwargs": {"count": 3}}

    # Test serialization round-trip
    serialized = queue.serializer.dumps(envelope)
    deserialized = queue.serializer.loads(serialized)

    # Verify the deserialized payload works
    func = deserialized["func"]
    args = deserialized["args"]
    kwargs = deserialized["kwargs"]
    result = func(*args, **kwargs)
    assert result == "Hello Alice! Count: 3"


def test_worker_serializer_round_trip():
    """Test that Worker can properly serialize and deserialize task payloads."""
    worker = Worker()

    def example_func(x, y):
        return x + y

    # Create a task payload as it would be received from backend
    envelope = {"func": example_func, "args": (5, 7), "kwargs": {}}

    # Test serialization round-trip
    serialized = worker.serializer.dumps(envelope)
    deserialized = worker.serializer.loads(serialized)

    # Verify the deserialized payload works
    func = deserialized["func"]
    args = deserialized["args"]
    kwargs = deserialized["kwargs"]
    result = func(*args, **kwargs)
    assert result == 12
