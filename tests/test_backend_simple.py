"""
Simple unit tests for SQLiteBackend functionality.
"""

import asyncio
import tempfile
from datetime import datetime, timezone

# Import from the source we created
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sitq.backends.sqlite import SQLiteBackend
from sitq.backends.base import ReservedTask, Result


def test_basic_functionality():
    """Test basic backend functionality without async."""
    with tempfile.TemporaryDirectory() as temp_dir:
        from pathlib import Path
        
        db_path = Path(temp_dir) / "test.db"
        
        # Test SQLiteBackend can be instantiated
        backend = SQLiteBackend(db_path)
        assert backend.database_path == db_path
        
        # Test that _get_connection method works
        conn = asyncio.run(backend._get_connection())
        assert conn is not None
        
        # Check that table creation works
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='tasks'
        """)
        assert cursor.fetchone() is not None
        
        asyncio.run(backend.close())


def test_data_models():
    """Test data model creation."""
    
    # Test ReservedTask creation
    task = ReservedTask(
        task_id="test_task",
        payload=b"test_payload",
        started_at=datetime.now(timezone.utc)
    )
    assert task.task_id == "test_task"
    assert task.payload == b"test_payload"
    assert task.started_at is not None
    
    # Test Result creation
    result = Result(
        task_id="test_task",
        status="success",
        value="test_result",
        error=None,
        traceback=None,
        finished_at=datetime.now(timezone.utc)
    )
    assert result.task_id == "test_task"
    assert result.status == "success"
    assert result.value == "test_result"


def test_async_enqueue_reserve():
    """Test async enqueue and reserve functionality."""
    async def run_test():
        with tempfile.TemporaryDirectory() as temp_dir:
            from pathlib import Path
            
            db_path = Path(temp_dir) / "test.db"
            backend = SQLiteBackend(db_path)
            
            # Test enqueue
            task_id = "test_task_1"
            payload = b"test_payload"
            available_at = datetime.now(timezone.utc)
            
            await backend.enqueue(task_id, payload, available_at)
            
            # Verify task was stored
            conn = await backend._get_connection()
            cursor = conn.execute("""
                SELECT task_id, payload, status FROM tasks WHERE task_id = ?
            """, (task_id,))
            
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == task_id
            assert row[1] == payload
            assert row[2] == 'pending'
            
            # Test reserve
            reserved = await backend.reserve(1, available_at)
            assert len(reserved) == 1
            assert reserved[0].task_id == task_id
            assert reserved[0].payload == payload
            
            await backend.close()
    
    asyncio.run(run_test())


def test_result_tracking():
    """Test result tracking functionality."""
    async def run_test():
        with tempfile.TemporaryDirectory() as temp_dir:
            from pathlib import Path
            
            db_path = Path(temp_dir) / "test.db"
            backend = SQLiteBackend(db_path)
            
            # Enqueue and reserve a task
            task_id = "test_task_1"
            payload = b"test_payload"
            now = datetime.now(timezone.utc)
            
            await backend.enqueue(task_id, payload, now)
            await backend.reserve(1, now)
            
            # Test mark_success
            result_value = "test_result"
            finished_at = datetime.now(timezone.utc)
            await backend.mark_success(task_id, result_value, finished_at)
            
            # Get result
            result = await backend.get_result(task_id)
            assert result is not None
            assert result.task_id == task_id
            assert result.status == "success"
            assert result.value == result_value
            
            await backend.close()
    
    asyncio.run(run_test())


if __name__ == "__main__":
    print("Running backend tests...")
    
    print("Testing basic functionality...")
    test_basic_functionality()
    print("✓ Basic functionality test passed")
    
    print("Testing data models...")
    test_data_models()
    print("✓ Data models test passed")
    
    print("Testing async enqueue/reserve...")
    test_async_enqueue_reserve()
    print("✓ Async enqueue/reserve test passed")
    
    print("Testing result tracking...")
    test_result_tracking()
    print("✓ Result tracking test passed")
    
    print("All backend tests passed!")
