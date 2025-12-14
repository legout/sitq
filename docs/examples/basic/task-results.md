# Task Results

Learn how to retrieve and work with results from completed tasks, including handling timeouts and error cases.

## What You'll Learn

- How to retrieve task results using `get_result()`
- Understanding Result objects and their properties
- Handling successful and failed task results
- Working with timeouts and waiting strategies

## Prerequisites

- Complete [Task Arguments](./task-arguments.md) first
- Understanding of Python exceptions and error handling

## Code Example

```python
import asyncio
from sitq import TaskQueue, Worker, Result
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer

# Step 1: Define tasks with different outcomes
async def successful_task(task_id: int, data: str):
    """A task that completes successfully."""
    await asyncio.sleep(0.5)
    result = f"Processed '{data}' with ID {task_id}"
    print(f"✓ Task {task_id} completed: {result}")
    return result

async def failing_task(task_id: int):
    """A task that intentionally fails."""
    await asyncio.sleep(0.3)
    print(f"✗ Task {task_id} failing...")
    raise ValueError(f"Intentional failure for task {task_id}")

async def slow_task(task_id: int):
    """A task that takes a long time."""
    await asyncio.sleep(3.0)  # This will timeout
    return f"Slow task {task_id} result"

async def data_processing_task(task_id: int, numbers: list):
    """A task that processes data and returns structured results."""
    await asyncio.sleep(0.8)
    if not numbers:
        return {"error": "No data provided"}

    result = {
        "task_id": task_id,
        "input_count": len(numbers),
        "sum": sum(numbers),
        "average": sum(numbers) / len(numbers),
        "max": max(numbers),
        "min": min(numbers),
        "processed_at": "2024-01-01T12:00:00Z"
    }
    print(f"✓ Task {task_id} processed {len(numbers)} numbers")
    return result

# Step 2: Helper function to check result status
def analyze_result(result: Result, task_id: str):
    """Analyze and display result information."""
    print(f"\n--- Result Analysis for Task {task_id} ---")

    if result.is_success():
        print("✓ Status: SUCCESS")
        print(f"✓ Value: {result.value}")
        print(f"✓ Finished at: {result.finished_at}")
    elif result.is_failed():
        print("✗ Status: FAILED")
        print(f"✗ Error: {result.error}")
        if result.traceback:
            print(f"✗ Traceback: {result.traceback}")
    else:
        print("? Status: UNKNOWN")
        print(f"Raw result: {result}")

async def main():
    # Step 3: Set up the queue
    backend = SQLiteBackend("results_queue.db")
    serializer = CloudpickleSerializer()
    queue = TaskQueue(backend, serializer)
    await queue.connect()

    # Create and start worker
    worker = Worker(backend, serializer)
    await worker.start()

    print("=== Task Results Example ===\n")

    # Step 4: Demonstrate successful task results
    print("1. Testing successful task results:")
    task_id1 = await queue.enqueue(successful_task, 1, "hello world")
    task_id2 = await queue.enqueue(data_processing_task, 2, [1, 2, 3, 4, 5])

    # Wait for completion and retrieve results
    await asyncio.sleep(1.0)

    result1 = await queue.get_result(task_id1, timeout=5)
    result2 = await queue.get_result(task_id2, timeout=5)

    analyze_result(result1, "1")
    analyze_result(result2, "2")

    # Step 5: Demonstrate failed task results
    print("\n2. Testing failed task results:")
    task_id3 = await queue.enqueue(failing_task, 3)
    await asyncio.sleep(1.0)

    result3 = await queue.get_result(task_id3, timeout=5)
    analyze_result(result3, "3")

    # Step 6: Demonstrate timeout handling
    print("\n3. Testing timeout scenarios:")

    # Task that will timeout (takes 3 seconds, we wait 1 second)
    task_id4 = await queue.enqueue(slow_task, 4)
    print("Enqueued slow task (3 seconds)...")

    try:
        result4 = await queue.get_result(task_id4, timeout=1)
        print(f"Got result (unexpected): {result4}")
    except asyncio.TimeoutError:
        print("✓ Timeout working correctly - task still processing")

    # Wait for the task to actually complete
    await asyncio.sleep(3.0)
    result4 = await queue.get_result(task_id4, timeout=5)
    analyze_result(result4, "4")

    # Step 7: Demonstrate result polling strategy
    print("\n4. Testing result polling:")

    async def poll_for_result(task_id: str, max_attempts: int = 10, delay: float = 0.5):
        """Poll for task completion with timeout."""
        for attempt in range(max_attempts):
            result = await queue.get_result(task_id, timeout=1)
            if result and (result.is_success() or result.is_failed()):
                return result
            print(f"  Attempt {attempt + 1}: Task still processing...")
            await asyncio.sleep(delay)
        return None

    task_id5 = await queue.enqueue(data_processing_task, 5, [10, 20, 30])
    print("Polling for task completion...")
    result5 = await poll_for_result(task_id5)
    analyze_result(result5, "5")

    # Step 8: Demonstrate batch result collection
    print("\n5. Testing batch result collection:")

    # Enqueue multiple tasks
    batch_tasks = []
    for i in range(6, 9):
        task_id = await queue.enqueue(data_processing_task, i, [i, i*2, i*3])
        batch_tasks.append(task_id)

    print(f"Enqueued {len(batch_tasks)} tasks for batch processing")

    # Wait and collect all results
    await asyncio.sleep(2.0)

    batch_results = []
    for task_id in batch_tasks:
        result = await queue.get_result(task_id, timeout=5)
        batch_results.append((task_id, result))

    print(f"\nBatch Results Summary:")
    for task_id, result in batch_results:
        if result and result.is_success():
            print(f"  Task {task_id}: ✓ {result.value['input_count']} numbers processed")
        else:
            print(f"  Task {task_id}: ✗ Failed or incomplete")

    # Step 9: Cleanup
    await worker.stop()
    await queue.close()
    print("\n=== Example completed ===")

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Concepts

### Result Object
The `Result` object contains information about task execution:

- **status**: Task execution status (success, failed, pending)
- **value**: Return value from successful tasks
- **error**: Error message from failed tasks
- **traceback**: Full exception traceback for debugging
- **enqueued_at/finished_at**: Timestamps for execution tracking

### Result Methods
- `result.is_success()`: Check if task completed successfully
- `result.is_failed()`: Check if task failed with an error
- `result.is_pending()`: Check if task is still processing

### Timeout Handling
- `queue.get_result(task_id, timeout=seconds)`: Wait up to timeout seconds
- `asyncio.TimeoutError`: Raised when timeout expires
- Use polling strategies for long-running tasks

### Best Practices

**For short tasks:**
```python
result = await queue.get_result(task_id, timeout=10)
if result and result.is_success():
    process_result(result.value)
```

**For long tasks:**
```python
result = None
while not result:
    result = await queue.get_result(task_id, timeout=1)
    if not result:
        print("Still processing...")
        await asyncio.sleep(1)
```

## Try It Yourself

1. **Experiment with different timeout values:**
   - Very short timeouts (0.1 seconds)
   - Very long timeouts (60 seconds)
   - No timeout (remove timeout parameter)

2. **Create custom result types:**
   - Return dictionaries with specific keys
   - Return custom class instances
   - Return None and handle it appropriately

3. **Test error scenarios:**
   - Tasks that raise different exception types
   - Tasks with circular references
   - Tasks that return unserializable objects

## Next Steps

- Learn about [Error Handling](./error-handling.md) for robust task processing
- Explore [Task Status](./task-status.md) for monitoring task progress
- See [Batch Processing](./batch-processing.md) for efficient bulk result collection