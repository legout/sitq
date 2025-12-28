#!/usr/bin/env python3
"""Test to verify Phase 2 fixes."""

import asyncio
import tempfile

from sitq import TaskQueue, SQLiteBackend
from sitq.exceptions import TaskExecutionError


async def test_timeout_zero():
    """Test that timeout=0 returns immediately if no result."""
    print("Testing timeout=0 semantics...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    backend = SQLiteBackend(db_path)
    await backend.connect()
    queue = TaskQueue(backend)

    # Try to get result for non-existent task with timeout=0
    # Should return None immediately, not wait forever
    result = await queue.get_result("nonexistent-task-id", timeout=0)
    assert result is None, "timeout=0 should return None immediately"

    print("✓ timeout=0 returns None immediately")

    # Test with timeout=None (should wait indefinitely)
    # We won't actually test this as it would hang

    # Test with timeout=0.1 (normal case)
    result = await queue.get_result("nonexistent-task-id", timeout=0.1)
    assert result is None, "timeout=0.1 should return None quickly"

    print("✓ timeout=0.1 returns None quickly")

    await backend.close()
    import os

    os.unlink(db_path)


async def test_sqlite_error_column():
    """Test that SQLite backend has error column."""
    print("\nTesting SQLite error column...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    backend = SQLiteBackend(db_path)
    await backend.connect()
    queue = TaskQueue(backend)

    async def failing_task():
        raise ValueError("This task always fails")

    # Enqueue a task that will fail
    task_id = await queue.enqueue(failing_task)

    # Start a worker to process it
    from sitq import Worker

    worker = Worker(backend, max_concurrency=1, poll_interval=0.01)
    worker_task = asyncio.create_task(worker.start())

    # Wait for result (should be failed)
    result = await queue.get_result(task_id, timeout=5.0)

    await worker.stop()
    await worker_task

    assert result is not None, "Should have a result"
    assert result.status == "failed", "Task should have failed"
    # The error column should now exist and contain the error message
    assert result.error is not None, "Error column should contain error message"

    print(f"✓ Error column exists and contains: {result.error}")

    await backend.close()
    import os

    os.unlink(db_path)


async def test_migration():
    """Test that migration adds error column to existing DB."""
    print("\nTesting schema migration...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    # Create a database without the error column (simulate old version)
    import sqlalchemy as sa
    from sqlalchemy import create_engine, Column, String, LargeBinary, Table, MetaData

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as conn:
        # Create results table without error column (old schema)
        metadata = MetaData()
        results = Table(
            "results",
            metadata,
            Column("id", String, primary_key=True),
            Column("task_id", String),
            Column("status", String, nullable=False),
            Column("value", LargeBinary, nullable=True),
            # No error column!
            Column("traceback", String, nullable=True),
        )
        metadata.create_all(bind=conn)

    # Now connect with SQLiteBackend (should migrate)
    backend = SQLiteBackend(db_path)
    await backend.connect()
    queue = TaskQueue(backend)

    async def failing_task():
        raise ValueError("Migration test error")

    # Enqueue and execute a failing task
    task_id = await queue.enqueue(failing_task)

    from sitq import Worker

    worker = Worker(backend, max_concurrency=1, poll_interval=0.01)
    worker_task = asyncio.create_task(worker.start())

    result = await queue.get_result(task_id, timeout=5.0)

    await worker.stop()
    await worker_task

    assert result is not None, "Should have a result"
    assert result.status == "failed", "Task should have failed"
    assert result.error is not None, "Error column should exist after migration"

    print(f"✓ Migration successful: error column added")

    await backend.close()
    engine.dispose()
    import os

    os.unlink(db_path)


if __name__ == "__main__":
    print("Running Phase 2 verification tests...\n")
    asyncio.run(test_timeout_zero())
    asyncio.run(test_sqlite_error_column())
    asyncio.run(test_migration())
    print("\n✓ All Phase 2 tests passed!")
