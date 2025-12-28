# Quickstart

Get started with sitq in just a few minutes. This guide will walk you through creating your first task queue and processing tasks.

## Current API Overview

sitq provides an async-first task queue with the following core components:

- `TaskQueue` - Async queue for enqueuing and retrieving tasks
- `Worker` - Worker for processing tasks from queue  
- `SQLiteBackend` - SQLite backend for task persistence
- `CloudpickleSerializer` - Default serialization for tasks/results

## Basic Usage Pattern

```python
import asyncio
from sitq import TaskQueue, Worker, SQLiteBackend

async def my_task(name: str) -> str:
    """Example task function."""
    await asyncio.sleep(0.1)  # Simulate work
    return f"Hello, {name}!"

async def main():
    # 1. Set up backend and queue
    backend = SQLiteBackend("tasks.db")
    queue = TaskQueue(backend=backend)
    
    # 2. Enqueue a task
    task_id = await queue.enqueue(my_task, "World")
    print(f"Enqueued task: {task_id}")
    
    # 3. Start worker to process tasks
    worker = Worker(backend, max_concurrency=2)
    
    try:
        # Start worker in background
        worker_task = asyncio.create_task(worker.start())
        
        # Give worker time to process
        await asyncio.sleep(2)
        
        # 4. Get result
        result = await queue.get_result(task_id, timeout=5)
        if result and result.status == "success":
            value = queue.deserialize_result(result)
            print(f"Result: {value}")
        
    finally:
        await worker.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Runnable Examples

See the `examples/basic/` directory for working examples:

```bash
# API structure verification
python examples/basic/api_demo.py

# When backend issues are resolved, try:
python examples/basic/quickstart_simple.py
```

## Key Concepts

### TaskQueue
The primary interface for enqueuing tasks and retrieving results:

```python
# Enqueue a task
task_id = await queue.enqueue(function, *args, **kwargs)

# Get a result
result = await queue.get_result(task_id, timeout=30)

# Deserialize result value
value = queue.deserialize_result(result)
```

### Worker
Processes tasks from the queue with configurable concurrency:

```python
# Create worker
worker = Worker(backend, max_concurrency=4)

# Start/stop worker
await worker.start()
await worker.stop()
```

### SQLiteBackend
Provides SQLite-based task persistence:

```python
# In-memory database (for testing)
backend = SQLiteBackend(":memory:")

# File-based database (for persistence)
backend = SQLiteBackend("tasks.db")
```

## Current Implementation Status

**✅ Working Features:**
- Core task queue operations (enqueue, get_result)
- Worker with async/sync function support
- SQLite backend with basic persistence
- Cloudpickle serialization
- Comprehensive error handling

**🔧 Under Development:**
- Full end-to-end task processing (backend fixes in progress)
- Additional backends (PostgreSQL, Redis, NATS)
- Advanced retry policies and scheduling
- Performance optimizations

## Next Steps

- [Basic Concepts](basic-concepts.md) - Learn about the architecture
- [Task Queues](../user-guide/task-queues.md) - Deep dive into queue management
- [Workers](../user-guide/workers.md) - Advanced worker configuration
- [Examples](../user-guide/examples/) - Real-world usage patterns

## Troubleshooting

**Import Error**: Make sure sitq is installed:
```bash
pip install -e .
```

**Database Error**: Check that the SQLite backend path is accessible:
```python
# Use absolute path for file-based storage
backend = SQLiteBackend("/full/path/to/tasks.db")
```

**Task Processing Issues**: Check worker and result status:
```python
result = await queue.get_result(task_id, timeout=5)
if result and result.status == "success":
    value = queue.deserialize_result(result)
    print(f"Task succeeded: {value}")
elif result:
    print(f"Task failed: {result.error}")
else:
    print("Task timed out")
```

## Running the Example

Save the code above as `quickstart_example.py` and run:

```bash
python quickstart_example.py
```

Expected output:
```
Enqueued task: 1
Enqueued task: 2
Enqueued task: 3
Enqueued task: 4
Enqueued task: 5

Processing tasks:
Task 1: Processed: data_0
Task 2: Processed: data_1
Task 3: Processed: data_2
Task 4: Processed: data_3
Task 5: Processed: data_4
```

## Key Concepts

### Tasks
Tasks are units of work that can be executed asynchronously:

```python
task = sitq.Task(
    function=my_function,      # Function to execute
    args=[arg1, arg2],         # Positional arguments
    kwargs={"key": "value"}    # Keyword arguments
)
```

### Backends
Backends provide storage for tasks and results:

```python
# In-memory SQLite (for testing)
backend = sitq.SQLiteBackend(":memory:")

# File-based SQLite (for persistence)
backend = sitq.SQLiteBackend("tasks.db")
```

### Workers
Workers execute tasks from the queue:

```python
worker = sitq.Worker(queue)

# Process a single task
result = worker.process_task(task_id)

# Process tasks continuously
worker.run()
```

## Next Steps

- [Basic Concepts](basic-concepts.md) - Learn about the architecture
- [Task Queues](../user-guide/task-queues.md) - Deep dive into queue management
- [Workers](../user-guide/workers.md) - Advanced worker configuration
- [Examples](../user-guide/examples/) - Real-world usage patterns

## Troubleshooting

**Import Error**: Make sure sitq is installed:
```bash
pip install sitq
```

**Database Error**: Check that the SQLite backend path is accessible:
```python
# Use absolute path for file-based storage
backend = sitq.SQLiteBackend("/full/path/to/tasks.db")
```

**Task Fails**: Check the result for errors:
```python
result = worker.process_task(task_id)
if result.is_error:
    print(f"Task failed: {result.error}")
else:
    print(f"Task succeeded: {result.value}")
```