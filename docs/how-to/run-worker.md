# Running Workers

Workers execute tasks from the queue. This guide shows how to start, configure, and manage workers effectively.

## Basic Worker Setup

Create a worker with a backend:

```python
from sitq import Worker, SQLiteBackend

backend = SQLiteBackend("tasks.db")
worker = Worker(backend)
```

## Starting and Stopping Workers

### Run Worker for a Duration

```python
import asyncio

async def main():
    # Start worker in background
    worker_task = asyncio.create_task(worker.start())
    
    # Let worker process tasks for a while
    await asyncio.sleep(10)
    
    # Stop worker gracefully
    await worker.stop()

asyncio.run(main())
```

### Run Worker with Async Context Manager

```python
async def main():
    async with backend:
        worker_task = asyncio.create_task(worker.start())
        await asyncio.sleep(10)
        await worker.stop()

asyncio.run(main())
```

## Worker Configuration

### Concurrency Control

Limit maximum concurrent tasks:

```python
# Execute at most 2 tasks simultaneously
worker = Worker(backend, max_concurrency=2)

# Execute at most 10 tasks simultaneously
worker = Worker(backend, max_concurrency=10)
```

See [Concurrency Control](../tutorials/concurrency.md) for detailed guidance on choosing limits.

### Polling Interval

Control how often worker checks for new tasks:

```python
# Poll every 0.5 seconds (default is 1.0)
worker = Worker(backend, poll_interval=0.5)

# Poll every 2 seconds
worker = Worker(backend, poll_interval=2.0)
```

Shorter intervals mean faster task pickup but higher CPU usage. Longer intervals reduce CPU usage but may delay task execution.

### Custom Serialization

Use a custom serializer:

```python
from sitq.serialization import Serializer

class MySerializer(Serializer):
    def dumps(self, obj):
        # Custom serialization logic
        return custom_serialize(obj)
    
    def loads(self, data):
        # Custom deserialization logic
        return custom_deserialize(data)

worker = Worker(backend, serializer=MySerializer())
```

## Running Multiple Workers

For higher throughput, run multiple workers:

```python
async def main():
    workers = []
    
    # Create 4 workers
    for i in range(4):
        worker = Worker(backend, max_concurrency=2)
        workers.append(worker)
    
    # Start all workers
    worker_tasks = []
    for worker in workers:
        task = asyncio.create_task(worker.start())
        worker_tasks.append(task)
    
    # Let workers process tasks
    await asyncio.sleep(60)
    
    # Stop all workers
    for worker in workers:
        await worker.stop()
    
    # Wait for worker tasks to complete
    await asyncio.gather(*worker_tasks, return_exceptions=True)

asyncio.run(main())
```

## Worker Lifecycle

### Starting Workers

[`Worker.start()`](../reference/api/sitq.worker.md) begins the polling loop:

```python
worker_task = asyncio.create_task(worker.start())
```

The worker will:
1. Poll the backend for pending tasks
2. Reserve tasks up to `max_concurrency` limit
3. Execute reserved tasks concurrently
4. Store results back to backend
5. Repeat until stopped

### Stopping Workers

Always stop workers cleanly:

```python
try:
    worker_task = asyncio.create_task(worker.start())
    await asyncio.sleep(10)
finally:
    await worker.stop()
```

[`Worker.stop()`](../reference/api/sitq.worker.md):
- Waits for currently running tasks to complete
- Does not accept new tasks
- Shuts down gracefully

## Common Patterns

### Single Task Execution

For one-off tasks, start a worker briefly:

```python
async def run_single_task():
    # Enqueue task
    task_id = await queue.enqueue(my_function, "arg")
    
    # Start worker just for this task
    worker_task = asyncio.create_task(worker.start())
    
    # Wait for task completion
    while True:
        result = await queue.get_result(task_id)
        if result:
            break
        await asyncio.sleep(0.1)
    
    await worker.stop()
    
    return result
```

### Continuous Processing

For ongoing task processing:

```python
async def run_continuously():
    try:
        worker_task = asyncio.create_task(worker.start())
        
        # Run indefinitely (or until shutdown signal)
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await worker.stop()
```

### Specialized Workers

Create different workers for different task types:

```python
# High-concurrency worker for I/O tasks
io_worker = Worker(backend, max_concurrency=50, poll_interval=0.5)

# Low-concurrency worker for CPU tasks
cpu_worker = Worker(backend, max_concurrency=4, poll_interval=1.0)

# Start both workers
await io_worker.start()
await cpu_worker.start()
```

## Troubleshooting

### Worker Not Starting

Ensure backend is properly initialized:

```python
# Make sure backend is connected
backend = SQLiteBackend("tasks.db")
queue = TaskQueue(backend=backend)

# Now create worker
worker = Worker(backend)
```

### Worker Not Processing Tasks

Check that tasks are enqueued:

```python
# Verify tasks are in queue
result = await queue.get_result(task_id)
if result is None:
    print("Task not found in queue")
```

### Worker Hanging

Set appropriate timeouts:

```python
# Use shorter poll intervals for testing
worker = Worker(backend, poll_interval=0.5)

# Or use in-memory backend for faster testing
backend = SQLiteBackend(":memory:")
```

## Best Practices

1. **Always stop workers** to ensure clean shutdown
2. **Use context managers** for automatic resource cleanup
3. **Monitor worker health** in production
4. **Set appropriate concurrency limits** based on workload
5. **Handle shutdown signals** gracefully

## What's Next?

- [Concurrency Control](../tutorials/concurrency.md) - Learn about bounded concurrency
- [Getting Results](get-results.md) - Retrieve task results
- [Handling Failures](handle-failures.md) - Error handling strategies
- [SQLite Backend](sqlite-backend.md) - Configure storage

## See Also

- [`Worker`](../reference/api/sitq.worker.md) - Worker API reference
- [Error Handling](error-handling.md) - Comprehensive error management
