"""Tests for TaskQueue core functionality."""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.sitq.queue import TaskQueue
from src.sitq.core import Result, Task, _now
from src.sitq.backends.base import Backend


class MockBackend(Backend):
    """Mock backend for testing."""

    def __init__(self):
        self.tasks = {}
        self.results = {}
        self.connected = False

    async def connect(self):
        self.connected = True

    async def close(self):
        self.connected = False

    async def enqueue(self, task: Task):
        self.tasks[task.id] = task

    async def fetch_due_tasks(self, limit: int = 1):
        return []

    async def update_task_state(self, task_id: str, **kwargs):
        if task_id in self.tasks:
            for key, value in kwargs.items():
                setattr(self.tasks[task_id], key, value)

    async def store_result(self, result: Result):
        self.results[result.task_id] = result

    async def get_result(self, task_id: str):
        return self.results.get(task_id)

    async def claim_task(self, task_id: str, lock_timeout: int = 30):
        return True

    async def release_task(self, task_id: str):
        pass

    async def schedule_retry(self, task_id: str, delay: int):
        pass


@pytest.fixture
def mock_backend():
    return MockBackend()


@pytest.fixture
def task_queue(mock_backend):
    return TaskQueue(backend=mock_backend)


@pytest.mark.asyncio
async def test_taskqueue_enqueue_immediate_task(task_queue, mock_backend):
    """Test enqueueing a task without ETA (immediate execution)."""

    def test_func(x, y):
        return x + y

    # Enqueue task without ETA
    task_id = await task_queue.enqueue(test_func, 1, 2)

    # Verify task was stored
    assert task_id in mock_backend.tasks
    task = mock_backend.tasks[task_id]

    # Verify task structure
    assert task.func is not None
    assert task.available_at <= _now()

    # Verify envelope structure
    envelope = task_queue.serializer.loads(task.func)
    # Test that the function works correctly by calling it
    result = envelope["func"](*envelope["args"], **envelope["kwargs"])
    assert result == 3
    assert envelope["args"] == (1, 2)
    assert envelope["kwargs"] == {}


@pytest.mark.asyncio
async def test_taskqueue_enqueue_delayed_task(task_queue, mock_backend):
    """Test enqueueing a task with ETA (delayed execution)."""

    def test_func(name):
        return f"Hello {name}"

    # Schedule task for 1 hour in the future
    eta = _now() + timedelta(hours=1)
    task_id = await task_queue.enqueue(test_func, "World", eta=eta)

    # Verify task was stored
    assert task_id in mock_backend.tasks
    task = mock_backend.tasks[task_id]

    # Verify available_at is set to ETA
    assert task.available_at == eta

    # Verify envelope structure
    envelope = task_queue.serializer.loads(task.func)
    # Test that the function works correctly by calling it
    result = envelope["func"](*envelope["args"], **envelope["kwargs"])
    assert result == "Hello World"
    assert envelope["args"] == ("World",)
    assert envelope["kwargs"] == {}


@pytest.mark.asyncio
async def test_taskqueue_get_result_success(task_queue, mock_backend):
    """Test getting a successful result."""
    task_id = "test-task-123"

    # Create a successful result
    result = Result(
        task_id=task_id,
        status="success",
        value=b"42",
        enqueued_at=_now(),
        finished_at=_now(),
    )
    await mock_backend.store_result(result)

    # Get result
    retrieved_result = await task_queue.get_result(task_id)

    assert retrieved_result is not None
    assert retrieved_result.task_id == task_id
    assert retrieved_result.status == "success"
    assert retrieved_result.value == b"42"


@pytest.mark.asyncio
async def test_taskqueue_get_result_failure(task_queue, mock_backend):
    """Test getting a failed result."""
    task_id = "test-task-456"

    # Create a failed result
    result = Result(
        task_id=task_id,
        status="failed",
        error="Something went wrong",
        traceback="Traceback...",
        finished_at=_now(),
    )
    await mock_backend.store_result(result)

    # Get result
    retrieved_result = await task_queue.get_result(task_id)

    assert retrieved_result is not None
    assert retrieved_result.task_id == task_id
    assert retrieved_result.status == "failed"
    assert retrieved_result.error == "Something went wrong"
    assert retrieved_result.traceback == "Traceback..."
    assert retrieved_result.value is None


@pytest.mark.asyncio
async def test_taskqueue_get_result_timeout(task_queue, mock_backend):
    """Test getting result with timeout when result is not ready."""
    task_id = "test-task-789"

    # Don't store any result

    # Get result with short timeout
    result = await task_queue.get_result(task_id, timeout=1)

    assert result is None


@pytest.mark.asyncio
async def test_taskqueue_context_manager(task_queue, mock_backend):
    """Test TaskQueue as async context manager."""
    async with task_queue as tq:
        assert mock_backend.connected

    # Should be disconnected after context exit
    assert not mock_backend.connected


@pytest.mark.asyncio
async def test_taskqueue_close(task_queue, mock_backend):
    """Test closing TaskQueue."""
    # Initially not connected
    assert not mock_backend.connected

    # Connect and close
    await mock_backend.connect()
    await task_queue.close()

    assert not mock_backend.connected


@pytest.mark.asyncio
async def test_taskqueue_enqueue_with_kwargs(task_queue, mock_backend):
    """Test enqueueing task with keyword arguments."""

    def test_func(x, y, operation="add"):
        if operation == "add":
            return x + y
        elif operation == "multiply":
            return x * y
        return 0

    # Enqueue with kwargs
    task_id = await task_queue.enqueue(test_func, 3, 4, operation="multiply")

    # Verify task was stored
    assert task_id in mock_backend.tasks
    task = mock_backend.tasks[task_id]

    # Verify envelope structure
    envelope = task_queue.serializer.loads(task.func)
    # Test that function works correctly by calling it
    result = envelope["func"](*envelope["args"], **envelope["kwargs"])
    assert result == 12  # 3 * 4
    assert envelope["args"] == (3, 4)
    assert envelope["kwargs"] == {"operation": "multiply"}


@pytest.mark.asyncio
async def test_taskqueue_eta_timezone_aware(task_queue, mock_backend):
    """Test that ETA accepts timezone-aware datetime."""

    def test_func():
        return "test"

    # Create timezone-aware UTC datetime
    eta = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    task_id = await task_queue.enqueue(test_func, eta=eta)

    # Verify task was stored with correct ETA
    task = mock_backend.tasks[task_id]
    assert task.available_at == eta


@pytest.mark.asyncio
async def test_taskqueue_available_at_defaults_to_now(task_queue, mock_backend):
    """Test that available_at defaults to current time when no ETA provided."""

    def test_func():
        return "test"

    before_enqueue = _now()
    task_id = await task_queue.enqueue(test_func)
    after_enqueue = _now()

    # Verify available_at is between before and after enqueue
    task = mock_backend.tasks[task_id]
    assert before_enqueue <= task.available_at <= after_enqueue
