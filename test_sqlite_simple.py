"""Simple test for SQLite backend without fixtures."""

import asyncio
import tempfile
import uuid
from datetime import datetime, timezone

from src.sitq.backends.sqlite import SQLiteBackend
from src.sitq.core import Task


async def test_basic_operations():
    """Test basic SQLite backend operations."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        backend = SQLiteBackend(tmp.name)

        # Test initialization
        await backend.initialize()
        print("✓ Initialization successful")

        # Create a test task
        task = Task(
            id=str(uuid.uuid4()),
            func=b"test_function",
            args=b"[1, 2, 3]",
            kwargs=b'{"key": "value"}',
            context=b'{"worker_id": "test_worker"}',
            created_at=datetime.now(timezone.utc),
            max_retries=3,
        )

        # Test enqueue
        await backend.enqueue(task)
        print("✓ Enqueue successful")

        # Test reserve
        now = datetime.now(timezone.utc)
        reserved_tasks = await backend.reserve(1, now)
        assert len(reserved_tasks) == 1
        reserved = reserved_tasks[0]
        assert reserved.task_id == task.id
        assert reserved.func == task.func
        print("✓ Reserve successful")

        # Test mark success
        await backend.mark_success(task.id, b"test_result")
        result = await backend.get_result(task.id)
        assert result is not None
        assert result.value == b"test_result"
        print("✓ Mark success successful")

        # Test queue stats
        stats = await backend.get_queue_stats()
        assert stats["completed"] >= 1
        print("✓ Queue stats successful")

        print("All basic tests passed!")


if __name__ == "__main__":
    asyncio.run(test_basic_operations())
