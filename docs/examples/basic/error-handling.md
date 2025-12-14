# Error Handling

Learn how to handle task failures, implement retry logic, and create robust error handling patterns for production use.

## What You'll Learn

- Understanding task failure states and error types
- Implementing retry logic for transient failures
- Error classification and handling strategies
- Monitoring and logging task failures
- Dead letter queue patterns

## Prerequisites

- Complete [Task Results](./task-results.md) first
- Understanding of Python exception handling
- Basic knowledge of logging concepts

## Code Example

```python
import asyncio
import logging
from datetime import datetime
from sitq import TaskQueue, Worker, Result
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Step 1: Define tasks with different failure patterns
async def network_task(task_id: int, url: str, should_fail: bool = False):
    """Simulate a network operation that might fail."""
    logger.info(f"Task {task_id}: Simulating network request to {url}")
    await asyncio.sleep(0.5)

    if should_fail:
        raise ConnectionError(f"Network failed for task {task_id}")

    return f"Successfully fetched from {url}"

async def database_task(task_id: int, operation: str):
    """Simulate a database operation."""
    logger.info(f"Task {task_id}: Database {operation}")
    await asyncio.sleep(0.3)

    if operation == "invalid_query":
        raise ValueError(f"Invalid SQL query for task {task_id}")
    elif operation == "connection_lost":
        raise ConnectionError(f"Database connection lost for task {task_id}")

    return f"Database {operation} completed"

async def calculation_task(task_id: int, numbers: list):
    """Perform calculations that might fail."""
    logger.info(f"Task {task_id}: Calculating with {numbers}")

    if not numbers:
        raise ValueError("No numbers provided for calculation")

    result = sum(numbers) / len(numbers)
    return {"task_id": task_id, "average": result}

# Step 2: Implement retry decorator
def retry_on_failure(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator to automatically retry failed tasks."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            task_id = args[0] if args else kwargs.get('task_id', 'unknown')
            attempt = 0

            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    logger.warning(f"Task {task_id} attempt {attempt} failed: {e}")

                    if attempt >= max_attempts:
                        logger.error(f"Task {task_id} failed after {max_attempts} attempts")
                        raise

                    wait_time = delay * (backoff ** (attempt - 1))
                    logger.info(f"Retrying task {task_id} in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)

        return wrapper
    return decorator

# Step 3: Apply retry logic to tasks
@retry_on_failure(max_attempts=3, delay=0.5, backoff=2.0)
async def resilient_network_task(task_id: int, url: str):
    """Network task with automatic retry."""
    logger.info(f"Resilient task {task_id}: Attempting network request to {url}")
    await asyncio.sleep(0.5)

    # Simulate random failures
    import random
    if random.random() < 0.3:  # 30% failure rate
        raise ConnectionError(f"Network timeout for task {task_id}")

    return f"Successfully fetched from {url}"

# Step 4: Error classification
class TaskError(Exception):
    """Base class for task-specific errors."""
    pass

class TransientError(TaskError):
    """Temporary errors that might succeed on retry."""
    pass

class PermanentError(TaskError):
    """Errors that won't be resolved by retrying."""
    pass

async def smart_processing_task(task_id: int, data_type: str):
    """Task that distinguishes between transient and permanent errors."""
    logger.info(f"Smart task {task_id}: Processing {data_type}")

    if data_type == "transient_fail":
        # Simulate transient error (network glitch, etc.)
        await asyncio.sleep(0.2)
        raise TransientError(f"Transient error for task {task_id}")

    elif data_type == "permanent_fail":
        # Simulate permanent error (invalid data, etc.)
        await asyncio.sleep(0.1)
        raise PermanentError(f"Permanent error for task {task_id}")

    elif data_type == "eventual_success":
        # Simulate eventual success after retries
        await asyncio.sleep(0.1)
        raise TransientError(f"First attempt failed for task {task_id}")

    return f"Successfully processed {data_type}"

# Step 5: Main demonstration
async def main():
    backend = SQLiteBackend("error_handling_queue.db")
    serializer = CloudpickleSerializer()
    queue = TaskQueue(backend, serializer)
    await queue.connect()

    worker = Worker(backend, serializer)
    await worker.start()

    print("=== Error Handling Example ===\n")

    # Test 1: Basic failure handling
    print("1. Testing basic task failure:")
    task_id1 = await queue.enqueue(failing_task, 1)  # This will fail
    await asyncio.sleep(1.0)

    result1 = await queue.get_result(task_id1, timeout=5)
    if result1 and result1.is_failed():
        print(f"✓ Caught expected failure: {result1.error}")
    else:
        print("✗ Expected task to fail")

    # Test 2: Retry logic demonstration
    print("\n2. Testing retry logic:")
    for i in range(2, 5):
        task_id = await queue.enqueue(resilient_network_task, i, f"https://api.example.com/data/{i}")
        print(f"Enqueued resilient task {task_id}")

    await asyncio.sleep(5.0)  # Allow retries to complete

    # Check results
    for i in range(2, 5):
        result = await queue.get_result(f"resilient_task_{i}", timeout=1)
        # Note: In real implementation, you'd track the actual task IDs

    # Test 3: Error classification
    print("\n3. Testing error classification:")
    error_tasks = [
        ("transient_fail", "transient"),
        ("permanent_fail", "permanent"),
        ("eventual_success", "transient")
    ]

    for data_type, error_type in error_tasks:
        task_id = await queue.enqueue(smart_processing_task, 100, data_type)
        print(f"Enqueued {error_type} error task: {task_id}")

    await asyncio.sleep(3.0)

    # Test 4: Dead letter queue pattern
    print("\n4. Testing dead letter queue pattern:")

    failed_tasks = []

    # Simulate collecting failed tasks
    for i in range(5, 8):
        task_id = await queue.enqueue(failing_task, i)
        await asyncio.sleep(0.5)

        result = await queue.get_result(task_id, timeout=2)
        if result and result.is_failed():
            failed_tasks.append({
                'task_id': task_id,
                'error': result.error,
                'timestamp': datetime.now(),
                'retry_count': 0
            })

    print(f"Collected {len(failed_tasks)} failed tasks for manual review")

    # Test 5: Circuit breaker pattern simulation
    print("\n5. Testing circuit breaker simulation:")

    class SimpleCircuitBreaker:
        def __init__(self, failure_threshold: int = 3):
            self.failure_threshold = failure_threshold
            self.failure_count = 0
            self.last_failure_time = None
            self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

        def record_failure(self):
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")

        def record_success(self):
            self.failure_count = 0
            self.state = "CLOSED"

        def can_execute(self) -> bool:
            if self.state == "OPEN":
                # Simple time-based recovery
                if self.last_failure_time:
                    time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
                    if time_since_failure > 10:  # 10 second recovery window
                        self.state = "HALF_OPEN"
                        return True
                return False
            return True

    circuit_breaker = SimpleCircuitBreaker()

    # Test circuit breaker with failing tasks
    for i in range(8, 12):
        if circuit_breaker.can_execute():
            task_id = await queue.enqueue(failing_task, i)
            print(f"Circuit breaker CLOSED: Enqueued task {task_id}")

            # Simulate checking result
            await asyncio.sleep(0.5)
            result = await queue.get_result(task_id, timeout=2)

            if result and result.is_failed():
                circuit_breaker.record_failure()
            else:
                circuit_breaker.record_success()
        else:
            print(f"Circuit breaker OPEN: Skipping task {i}")

    # Cleanup
    await worker.stop()
    await queue.close()
    print("\n=== Error handling example completed ===")

# Helper function that doesn't exist - need to define it
async def failing_task(task_id: int):
    """A task that always fails for testing purposes."""
    await asyncio.sleep(0.2)
    raise ValueError(f"Intentional failure for task {task_id}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Concepts

### Error Types
- **Transient Errors**: Temporary issues that may resolve themselves (network timeouts, database locks)
- **Permanent Errors**: Issues that won't be fixed by retrying (invalid data, missing files)

### Retry Strategies
- **Fixed Delay**: Wait the same amount of time between retries
- **Exponential Backoff**: Increase wait time between retries
- **Maximum Attempts**: Limit retry attempts to prevent infinite loops

### Circuit Breaker Pattern
- **CLOSED**: Normal operation, allow requests
- **OPEN**: Stop requests due to high failure rate
- **HALF_OPEN**: Allow limited requests to test recovery

### Error Handling Best Practices

**For transient errors:**
```python
try:
    result = await risky_operation()
    return result
except (ConnectionError, TimeoutError) as e:
    logger.warning(f"Transient error: {e}")
    # Retry with exponential backoff
    await asyncio.sleep(1)
    return await risky_operation()
```

**For permanent errors:**
```python
try:
    result = await operation()
    validate_input(result)
    return result
except ValueError as e:
    logger.error(f"Permanent error: {e}")
    # Don't retry, handle as failure
    raise
```

## Try It Yourself

1. **Implement different retry strategies:**
   - Linear backoff (1s, 2s, 3s, ...)
   - Exponential backoff with jitter
   - Custom retry conditions based on error type

2. **Create a monitoring system:**
   - Track failure rates over time
   - Alert on unusual error patterns
   - Dashboard for failed task analysis

3. **Test edge cases:**
   - Tasks that succeed after many retries
   - Tasks that fail consistently
   - Network partitions and recovery

## Next Steps

- Learn about [Task Status](./task-status.md) for real-time monitoring
- Explore [Batch Processing](./batch-processing.md) for bulk operations with error handling
- See [Advanced Examples](../../advanced/) for production-grade patterns