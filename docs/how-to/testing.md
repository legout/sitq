# Testing Guide

This guide covers testing strategies, best practices, and tools used in sitq development.

## Testing Philosophy

### Testing Goals

1. **Reliability**: Ensure sitq works correctly under all conditions
2. **Performance**: Maintain performance standards
3. **Compatibility**: Test across Python versions and platforms
4. **Maintainability**: Make code easy to modify and extend

### Testing Pyramid

```
    ┌─────────────────┐
    │   E2E Tests     │  ← Few, slow, high value
    │  (Integration)  │
    └─────────────────┘
  ┌───────────────────────┐
  │  Integration Tests    │  ← Moderate number, medium speed
  │   (Component Tests)   │
  └───────────────────────┘
┌─────────────────────────────┐
│      Unit Tests            │  ← Many, fast, focused
│   (Function/Class Tests)   │
└─────────────────────────────┘
```

## Test Structure

### Directory Organization

```
tests/
├── unit/                    # Unit tests
│   ├── test_queue.py
│   ├── test_worker.py
│   ├── test_backends.py
│   └── test_serialization.py
├── integration/             # Integration tests
│   ├── test_queue_worker.py
│   ├── test_backend_integration.py
│   └── test_end_to_end.py
├── performance/             # Performance tests
│   ├── test_throughput.py
│   ├── test_latency.py
│   └── test_memory_usage.py
├── fixtures/               # Test data and utilities
│   ├── __init__.py
│   ├── sample_tasks.py
│   └── test_utils.py
└── conftest.py            # pytest configuration
```

### Test Configuration

```python
# conftest.py
import pytest
import tempfile
import os
from pathlib import Path

import sitq


@pytest.fixture(scope="session")
def test_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def memory_backend():
    """Create in-memory backend for testing."""
    return sitq.SQLiteBackend(":memory:")


@pytest.fixture
def file_backend(test_db):
    """Create file-based backend for testing."""
    backend = sitq.SQLiteBackend(test_db)
    yield backend
    backend.close()


@pytest.fixture
def task_queue(memory_backend):
    """Create task queue for testing."""
    return sitq.TaskQueue(backend=memory_backend)


@pytest.fixture
def worker(task_queue):
    """Create worker for testing."""
    return sitq.Worker(task_queue)


@pytest.fixture
def sample_task():
    """Create sample task for testing."""
    return sitq.Task(
        function=lambda x: x * 2,
        args=[5],
        metadata={"test": True}
    )
```

## Unit Testing

### Test Structure

```python
# tests/unit/test_queue.py
import pytest
from unittest.mock import Mock, patch

import sitq
from sitq.exceptions import QueueFullError, TaskNotFoundError


class TestTaskQueue:
    """Test suite for TaskQueue class."""
    
    def test_init_with_backend(self, memory_backend):
        """Test queue initialization with backend."""
        queue = sitq.TaskQueue(backend=memory_backend)
        assert queue.backend == memory_backend
    
    def test_enqueue_task(self, task_queue, sample_task):
        """Test task enqueuing."""
        task_id = task_queue.enqueue(sample_task)
        
        assert task_id is not None
        assert isinstance(task_id, str)
        assert len(task_id) > 0
    
    def test_enqueue_with_priority(self, task_queue):
        """Test task enqueuing with priority."""
        high_priority_task = sitq.Task(
            function=lambda: "high",
            priority=1
        )
        low_priority_task = sitq.Task(
            function=lambda: "low",
            priority=10
        )
        
        high_id = task_queue.enqueue(high_priority_task)
        low_id = task_queue.enqueue(low_priority_task)
        
        # High priority should be dequeued first
        first_task = task_queue.dequeue()
        assert first_task.id == high_id
    
    def test_get_task_status(self, task_queue, sample_task):
        """Test getting task status."""
        task_id = task_queue.enqueue(sample_task)
        status = task_queue.get_task_status(task_id)
        
        assert status in ["queued", "running", "completed", "failed"]
    
    def test_get_nonexistent_task(self, task_queue):
        """Test getting non-existent task raises error."""
        with pytest.raises(TaskNotFoundError):
            task_queue.get_task("nonexistent_id")
    
    @patch('time.time')
    def test_task_timestamps(self, mock_time, task_queue, sample_task):
        """Test task timestamps are recorded correctly."""
        mock_time.return_value = 1234567890.0
        
        task_id = task_queue.enqueue(sample_task)
        task = task_queue.get_task(task_id)
        
        assert task.created_at == 1234567890.0
    
    def test_queue_capacity_limit(self, task_queue):
        """Test queue respects capacity limits."""
        # Mock backend with capacity limit
        task_queue.backend.max_queue_size = 2
        
        task1 = sitq.Task(function=lambda: "task1")
        task2 = sitq.Task(function=lambda: "task2")
        task3 = sitq.Task(function=lambda: "task3")
        
        task_queue.enqueue(task1)
        task_queue.enqueue(task2)
        
        with pytest.raises(QueueFullError):
            task_queue.enqueue(task3)
```

### Mocking and Patching

```python
# tests/unit/test_worker.py
import pytest
from unittest.mock import Mock, patch, call

import sitq
from sitq.exceptions import WorkerError


class TestWorker:
    """Test suite for Worker class."""
    
    def test_worker_init(self, task_queue):
        """Test worker initialization."""
        worker = sitq.Worker(task_queue)
        assert worker.queue == task_queue
        assert worker.worker_id is not None
    
    @patch('sitq.worker.Worker.process_task')
    def test_run_processes_tasks(self, mock_process, worker):
        """Test worker processes tasks when running."""
        # Mock task processing
        mock_process.return_value = Mock(is_success=True)
        
        # Mock queue to return tasks then None
        worker.queue.dequeue = Mock(side_effect=[Mock(id="task1"), Mock(id="task2"), None])
        
        # Run for short duration
        with patch('time.sleep', side_effect=StopIteration):
            with pytest.raises(StopIteration):
                worker.run(duration=0.1)
        
        # Verify tasks were processed
        assert mock_process.call_count == 2
    
    def test_process_task_success(self, worker, sample_task):
        """Test successful task processing."""
        task_id = worker.queue.enqueue(sample_task)
        result = worker.process_task(task_id)
        
        assert result.is_success
        assert result.value == 10  # 5 * 2
    
    def test_process_task_with_exception(self, worker):
        """Test task processing with exception."""
        failing_task = sitq.Task(
            function=lambda: 1 / 0,  # Division by zero
            args=[]
        )
        
        task_id = worker.queue.enqueue(failing_task)
        result = worker.process_task(task_id)
        
        assert result.is_error
        assert "division by zero" in str(result.error)
    
    def test_process_task_with_retry(self, worker):
        """Test task processing with retry logic."""
        call_count = 0
        
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        retry_task = sitq.Task(
            function=flaky_function,
            max_retries=3,
            retry_delay=0.1
        )
        
        task_id = worker.queue.enqueue(retry_task)
        result = worker.process_task(task_id)
        
        assert result.is_success
        assert result.value == "success"
        assert call_count == 3
    
    @patch('sitq.worker.logger')
    def test_error_logging(self, mock_logger, worker):
        """Test errors are logged properly."""
        failing_task = sitq.Task(
            function=lambda: 1 / 0,
            args=[]
        )
        
        task_id = worker.queue.enqueue(failing_task)
        worker.process_task(task_id)
        
        # Verify error was logged
        mock_logger.error.assert_called()
        assert "Task failed" in str(mock_logger.error.call_args)
```

## Integration Testing

### Component Integration

```python
# tests/integration/test_queue_worker.py
import pytest
import time
import threading

import sitq


class TestQueueWorkerIntegration:
    """Test suite for queue-worker integration."""
    
    def test_end_to_end_task_processing(self):
        """Test complete task processing flow."""
        backend = sitq.SQLiteBackend(":memory:")
        queue = sitq.TaskQueue(backend=backend)
        worker = sitq.Worker(queue)
        
        # Create and enqueue task
        task = sitq.Task(
            function=lambda x: x ** 2,
            args=[7]
        )
        task_id = queue.enqueue(task)
        
        # Process task
        result = worker.process_task(task_id)
        
        # Verify result
        assert result.is_success
        assert result.value == 49
        
        # Verify task status
        status = queue.get_task_status(task_id)
        assert status == "completed"
    
    def test_concurrent_task_processing(self):
        """Test concurrent processing of multiple tasks."""
        backend = sitq.SQLiteBackend(":memory:")
        queue = sitq.TaskQueue(backend=backend)
        
        # Create multiple workers
        workers = [
            sitq.Worker(queue, worker_id=f"worker_{i}")
            for i in range(3)
        ]
        
        # Enqueue multiple tasks
        tasks = []
        for i in range(10):
            task = sitq.Task(
                function=lambda x, i=i: x + i,  # Capture i in closure
                args=[100]
            )
            task_id = queue.enqueue(task)
            tasks.append(task_id)
        
        # Start workers
        worker_threads = []
        for worker in workers:
            thread = threading.Thread(target=worker.run, kwargs={"duration": 2})
            thread.start()
            worker_threads.append(thread)
        
        # Wait for processing
        time.sleep(3)
        
        # Stop workers
        for worker in workers:
            worker.stop()
        
        for thread in worker_threads:
            thread.join()
        
        # Check results
        completed_tasks = 0
        for task_id in tasks:
            try:
                result = queue.get_result(task_id)
                if result.is_success:
                    completed_tasks += 1
            except sitq.TaskNotFoundError:
                pass
        
        assert completed_tasks == 10
    
    def test_worker_recovery_after_failure(self):
        """Test worker recovery after backend failure."""
        backend = sitq.SQLiteBackend(":memory:")
        queue = sitq.TaskQueue(backend=backend)
        worker = sitq.Worker(queue)
        
        # Simulate backend failure
        original_store = backend.store_result
        def failing_store(*args, **kwargs):
            if not hasattr(failing_store, 'call_count'):
                failing_store.call_count = 0
            failing_store.call_count += 1
            if failing_store.call_count == 1:
                raise sitq.BackendError("Simulated failure")
            return original_store(*args, **kwargs)
        
        backend.store_result = failing_store
        
        # Process task (should fail first time)
        task = sitq.Task(function=lambda: "test")
        task_id = queue.enqueue(task)
        
        # First attempt should fail
        with pytest.raises(sitq.BackendError):
            worker.process_task(task_id)
        
        # Second attempt should succeed
        result = worker.process_task(task_id)
        assert result.is_success
```

### Backend Integration

```python
# tests/integration/test_backend_integration.py
import pytest
import tempfile
import os

import sitq


class TestBackendIntegration:
    """Test suite for backend integration."""
    
    @pytest.mark.parametrize("backend_type", ["memory", "file"])
    def test_backend_persistence(self, backend_type):
        """Test backend persistence across restarts."""
        if backend_type == "memory":
            backend = sitq.SQLiteBackend(":memory:")
            persistent = False
        else:
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                db_path = f.name
            backend = sitq.SQLiteBackend(db_path)
            persistent = True
        
        queue = sitq.TaskQueue(backend=backend)
        
        # Create task
        task = sitq.Task(function=lambda: "persistent_test")
        task_id = queue.enqueue(task)
        
        # Process task
        worker = sitq.Worker(queue)
        result = worker.process_task(task_id)
        
        assert result.is_success
        assert result.value == "persistent_test"
        
        if persistent:
            # Close and reopen backend
            backend.close()
            new_backend = sitq.SQLiteBackend(db_path)
            new_queue = sitq.TaskQueue(backend=new_backend)
            
            # Task should still be accessible
            try:
                stored_result = new_queue.get_result(task_id)
                assert stored_result.value == "persistent_test"
            finally:
                new_backend.close()
                os.unlink(db_path)
    
    def test_concurrent_backend_access(self):
        """Test concurrent access to backend."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            backend = sitq.SQLiteBackend(db_path)
            queue = sitq.TaskQueue(backend=backend)
            
            def enqueue_tasks(worker_id):
                """Enqueue tasks from worker."""
                worker_queue = sitq.TaskQueue(backend=sitq.SQLiteBackend(db_path))
                for i in range(5):
                    task = sitq.Task(
                        function=lambda x, i=i: f"worker_{worker_id}_task_{i}",
                        args=[worker_id]
                    )
                    worker_queue.enqueue(task)
            
            # Start multiple threads enqueuing tasks
            threads = []
            for i in range(3):
                thread = threading.Thread(target=enqueue_tasks, args=(i,))
                thread.start()
                threads.append(thread)
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            # Verify all tasks were enqueued
            stats = queue.get_stats()
            assert stats.total_tasks == 15
            
        finally:
            backend.close()
            os.unlink(db_path)
```

## Performance Testing

### Throughput Testing

```python
# tests/performance/test_throughput.py
import pytest
import time
import statistics

import sitq


class TestThroughput:
    """Test suite for performance benchmarks."""
    
    def test_task_throughput(self):
        """Test task processing throughput."""
        backend = sitq.SQLiteBackend(":memory:")
        queue = sitq.TaskQueue(backend=backend)
        worker = sitq.Worker(queue)
        
        # Create many simple tasks
        num_tasks = 1000
        tasks = []
        for i in range(num_tasks):
            task = sitq.Task(
                function=lambda x, i=i: x + i,
                args=[1000]
            )
            tasks.append(task)
        
        # Measure enqueue time
        start_time = time.time()
        task_ids = queue.enqueue_batch(tasks)
        enqueue_time = time.time() - start_time
        
        # Measure processing time
        start_time = time.time()
        results = []
        for task_id in task_ids:
            result = worker.process_task(task_id)
            results.append(result)
        processing_time = time.time() - start_time
        
        # Calculate metrics
        enqueue_throughput = num_tasks / enqueue_time
        processing_throughput = num_tasks / processing_time
        
        print(f"Enqueue throughput: {enqueue_throughput:.2f} tasks/sec")
        print(f"Processing throughput: {processing_throughput:.2f} tasks/sec")
        
        # Assertions (adjust based on expected performance)
        assert enqueue_throughput > 100  # Should enqueue > 100 tasks/sec
        assert processing_throughput > 50  # Should process > 50 tasks/sec
        
        # Verify all tasks completed successfully
        successful_results = [r for r in results if r.is_success]
        assert len(successful_results) == num_tasks
    
    def test_memory_usage(self):
        """Test memory usage during processing."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        backend = sitq.SQLiteBackend(":memory:")
        queue = sitq.TaskQueue(backend=backend)
        worker = sitq.Worker(queue)
        
        # Process memory-intensive tasks
        large_data = list(range(10000))
        for i in range(100):
            task = sitq.Task(
                function=lambda data=large_data: len(data),
                args=[]
            )
            task_id = queue.enqueue(task)
            worker.process_task(task_id)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        print(f"Memory increase: {memory_increase / 1024 / 1024:.2f} MB")
        
        # Memory increase should be reasonable (adjust threshold as needed)
        assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase
    
    @pytest.mark.parametrize("num_workers", [1, 2, 4, 8])
    def test_scalability(self, num_workers):
        """Test scalability with multiple workers."""
        backend = sitq.SQLiteBackend(":memory:")
        queue = sitq.TaskQueue(backend=backend)
        
        # Create workers
        workers = [
            sitq.Worker(queue, worker_id=f"worker_{i}")
            for i in range(num_workers)
        ]
        
        # Enqueue CPU-bound tasks
        num_tasks = 100
        tasks = []
        for i in range(num_tasks):
            task = sitq.Task(
                function=lambda n=1000000: sum(range(n)),  # CPU-intensive
                args=[]
            )
            task_id = queue.enqueue(task)
            tasks.append(task_id)
        
        # Start all workers
        import threading
        threads = []
        start_time = time.time()
        
        for worker in workers:
            thread = threading.Thread(target=worker.run, kwargs={"duration": 30})
            thread.start()
            threads.append(thread)
        
        # Wait for all tasks to complete
        completed_tasks = 0
        while completed_tasks < num_tasks and time.time() - start_time < 30:
            completed_tasks = 0
            for task_id in tasks:
                try:
                    result = queue.get_result(task_id)
                    if result.is_success:
                        completed_tasks += 1
                except sitq.TaskNotFoundError:
                    pass
            time.sleep(0.1)
        
        total_time = time.time() - start_time
        
        # Stop workers
        for worker in workers:
            worker.stop()
        for thread in threads:
            thread.join()
        
        throughput = num_tasks / total_time
        print(f"Workers: {num_workers}, Throughput: {throughput:.2f} tasks/sec")
        
        # Verify all tasks completed
        assert completed_tasks == num_tasks
        
        # Throughput should scale with workers (with diminishing returns)
        if num_workers > 1:
            assert throughput > 10  # Minimum throughput expectation
```

## Test Utilities

### Fixtures and Helpers

```python
# tests/fixtures/test_utils.py
import time
import threading
from typing import List, Callable, Any

import sitq


class TaskGenerator:
    """Utility for generating test tasks."""
    
    @staticmethod
    def simple_task(value: Any):
        """Create a simple task."""
        return sitq.Task(
            function=lambda x: x,
            args=[value]
        )
    
    @staticmethod
    def cpu_task(iterations: int = 1000000):
        """Create a CPU-intensive task."""
        return sitq.Task(
            function=lambda n=iterations: sum(range(n)),
            args=[]
        )
    
    @staticmethod
    def io_task(duration: float = 0.1):
        """Create an I/O-bound task."""
        return sitq.Task(
            function=lambda d=duration: time.sleep(d) or f"slept_{d}",
            args=[]
        )
    
    @staticmethod
    def failing_task(exception: Exception = ValueError("Test error")):
        """Create a task that always fails."""
        return sitq.Task(
            function=lambda exc=exception: (_ for _ in ()).throw(exc),
            args=[]
        )


class WorkerManager:
    """Utility for managing multiple workers."""
    
    def __init__(self, queue: sitq.TaskQueue, num_workers: int = 1):
        self.queue = queue
        self.workers = [
            sitq.Worker(queue, worker_id=f"worker_{i}")
            for i in range(num_workers)
        ]
        self.threads = []
    
    def start(self, duration: float = None):
        """Start all workers."""
        for worker in self.workers:
            thread = threading.Thread(
                target=worker.run,
                kwargs={"duration": duration}
            )
            thread.start()
            self.threads.append(thread)
    
    def stop(self):
        """Stop all workers."""
        for worker in self.workers:
            worker.stop()
        for thread in self.threads:
            thread.join()
        self.threads.clear()
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def wait_for_completion(
    queue: sitq.TaskQueue,
    task_ids: List[str],
    timeout: float = 30.0
) -> List[sitq.Result]:
    """Wait for multiple tasks to complete."""
    start_time = time.time()
    results = []
    
    while time.time() - start_time < timeout:
        results = []
        all_completed = True
        
        for task_id in task_ids:
            try:
                result = queue.get_result(task_id)
                results.append(result)
            except sitq.TaskNotFoundError:
                all_completed = False
                break
        
        if all_completed:
            break
        
        time.sleep(0.1)
    
    return results


def assert_tasks_completed(task_ids: List[str], results: List[sitq.Result]):
    """Assert all tasks completed successfully."""
    assert len(task_ids) == len(results)
    
    for task_id, result in zip(task_ids, results):
        assert result.is_success, f"Task {task_id} failed: {result.error}"
```

## Continuous Integration

### CI Configuration

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: [3.8, 3.9, "3.10", "3.11"]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run linting
      run: |
        python -m flake8 src/sitq tests
        python -m black --check src/sitq tests
        python -m isort --check-only src/sitq tests
        python -m mypy src/sitq
    
    - name: Run tests
      run: |
        python -m pytest --cov=sitq --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Best Practices

### Test Design

1. **Arrange, Act, Assert**: Structure tests clearly
2. **One Assertion Per Test**: Focus on single behavior
3. **Descriptive Names**: Make test names self-documenting
4. **Independent Tests**: Tests should not depend on each other
5. **Repeatable**: Tests should produce same results every time

### Mocking Guidelines

1. **Mock External Dependencies**: Don't test external services
2. **Mock Interfaces**: Mock behavior, not implementation
3. **Verify Interactions**: Test that methods are called correctly
4. **Use Real Objects**: When possible, use real implementations

### Performance Testing

1. **Baseline Measurements**: Establish performance baselines
2. **Regression Testing**: Prevent performance regressions
3. **Environment Control**: Test in consistent environments
4. **Statistical Analysis**: Use statistical methods for results

## Next Steps

- [Contributing Guide](contributing.md) - Learn how to contribute
- [Performance Guide](performance.md) - Performance optimization
- [API Reference](../reference/api/) - Detailed API documentation