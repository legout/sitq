# Task Queues

Task queues are the central component of sitq, managing the lifecycle of tasks from creation to completion.

## Creating a Task Queue

```python
import sitq

# Basic task queue with SQLite backend
queue = sitq.TaskQueue(backend=sitq.SQLiteBackend("tasks.db"))

# In-memory queue for testing
queue = sitq.TaskQueue(backend=sitq.SQLiteBackend(":memory:"))
```

## Enqueuing Tasks

### Basic Task Creation

```python
def process_data(data, multiplier=1):
    """Process data with optional multiplier."""
    return data * multiplier

# Create a task
task = sitq.Task(
    function=process_data,
    args=[42],
    kwargs={"multiplier": 2}
)

# Enqueue the task
task_id = queue.enqueue(task)
print(f"Task enqueued: {task_id}")
```

### Batch Enqueue

```python
tasks = []
for i in range(10):
    task = sitq.Task(
        function=process_data,
        args=[i],
        kwargs={"multiplier": 10}
    )
    tasks.append(task)

# Enqueue multiple tasks at once
task_ids = queue.enqueue_batch(tasks)
print(f"Enqueued {len(task_ids)} tasks")
```

## Managing Tasks

### Task Status

```python
# Check task status
status = queue.get_task_status(task_id)
print(f"Task status: {status}")

# Possible statuses:
# - "queued": Task is waiting to be processed
# - "running": Task is currently being processed
# - "completed": Task finished successfully
# - "failed": Task failed with an error
```

### Getting Results

```python
# Get task result (blocks until completion)
result = queue.get_result(task_id)

if result.is_error:
    print(f"Task failed: {result.error}")
else:
    print(f"Task result: {result.value}")

# Get result with timeout
try:
    result = queue.get_result(task_id, timeout=30.0)
except sitq.TimeoutError:
    print("Task timed out")
```

### Non-blocking Result Check

```python
# Check if result is available without blocking
if queue.has_result(task_id):
    result = queue.get_result(task_id)
    print(f"Result ready: {result.value}")
else:
    print("Task still running")
```

## Queue Operations

### Queue Information

```python
# Get queue statistics
stats = queue.get_stats()
print(f"Total tasks: {stats.total_tasks}")
print(f"Queued tasks: {stats.queued_tasks}")
print(f"Running tasks: {stats.running_tasks}")
print(f"Completed tasks: {stats.completed_tasks}")

# List tasks by status
queued_tasks = queue.list_tasks(status="queued")
running_tasks = queue.list_tasks(status="running")
completed_tasks = queue.list_tasks(status="completed")
```

### Task Management

```python
# Cancel a queued task
if queue.can_cancel_task(task_id):
    queue.cancel_task(task_id)
    print(f"Task {task_id} cancelled")

# Retry a failed task
if queue.get_task_status(task_id) == "failed":
    queue.retry_task(task_id)
    print(f"Task {task_id} queued for retry")

# Delete old completed tasks
queue.delete_completed_tasks(older_than="7d")
```

## Advanced Configuration

### Custom Backend Configuration

```python
# SQLite with custom settings
backend = sitq.SQLiteBackend(
    database="production.db",
    connection_pool_size=10,
    connection_timeout=30.0
)

queue = sitq.TaskQueue(backend=backend)
```

### Task Priorities

```python
# High priority task (lower number = higher priority)
high_priority_task = sitq.Task(
    function=urgent_process,
    args=[critical_data],
    priority=1
)

# Low priority task
low_priority_task = sitq.Task(
    function=background_process,
    args=[normal_data],
    priority=10
)

# Enqueue with priorities
queue.enqueue(high_priority_task)   # Processed first
queue.enqueue(low_priority_task)     # Processed later
```

### Task Dependencies

```python
# Create dependent tasks
task1 = sitq.Task(function=step1, args=[data])
task2 = sitq.Task(function=step2, args=[data])
task3 = sitq.Task(function=step3, args=[data])

# Enqueue with dependencies
task1_id = queue.enqueue(task1)
task2_id = queue.enqueue(task2, depends_on=[task1_id])
task3_id = queue.enqueue(task3, depends_on=[task2_id])

# Tasks will be processed in dependency order
```

## Error Handling

### Task Error Handling

```python
def risky_operation(data):
    """Operation that might fail."""
    if data < 0:
        raise ValueError("Data cannot be negative")
    return data * 2

# Create task with retry configuration
task = sitq.Task(
    function=risky_operation,
    args=[-5],
    max_retries=3,
    retry_delay=1.0
)

task_id = queue.enqueue(task)

# Check for errors
result = queue.get_result(task_id)
if result.is_error:
    print(f"Task failed after {result.retry_count} retries")
    print(f"Error: {result.error}")
```

### Queue Error Handling

```python
try:
    task_id = queue.enqueue(task)
except sitq.QueueFullError:
    print("Queue is full, try again later")
except sitq.SerializationError as e:
    print(f"Cannot serialize task: {e}")
except sitq.BackendError as e:
    print(f"Backend error: {e}")
```

## Performance Optimization

### Batching Operations

```python
# Batch enqueue for better performance
tasks = [sitq.Task(function=process, args=[i]) for i in range(1000)]
task_ids = queue.enqueue_batch(tasks)

# Batch result retrieval
results = queue.get_results(task_ids)
```

### Connection Pooling

```python
# Configure connection pooling for better performance
backend = sitq.SQLiteBackend(
    database="high_volume.db",
    connection_pool_size=20,
    max_overflow=10
)

queue = sitq.TaskQueue(backend=backend)
```

## Monitoring and Debugging

### Task History

```python
# Get task history
history = queue.get_task_history(task_id)
print(f"Created: {history.created_at}")
print(f"Started: {history.started_at}")
print(f"Completed: {history.completed_at}")
print(f"Duration: {history.duration}")
```

### Queue Monitoring

```python
# Monitor queue health
health = queue.health_check()
print(f"Queue healthy: {health.is_healthy}")
print(f"Backend status: {health.backend_status}")
print(f"Active connections: {health.active_connections}")
```

## Best Practices

1. **Use appropriate backends**: SQLite for most cases, in-memory for testing
2. **Handle errors gracefully**: Always check `result.is_error`
3. **Use batching**: Batch operations for better performance
4. **Monitor queue size**: Prevent memory issues with large queues
5. **Set timeouts**: Avoid infinite waits with `get_result(timeout=...)`
6. **Clean up old tasks**: Regularly delete old completed tasks

## Next Steps

- [Workers Guide](workers.md) - Learn about task execution
- [Backends Guide](backends.md) - Explore storage options
- [Serialization Guide](serialization.md) - Understand data handling
- [Error Handling Guide](error-handling.md) - Comprehensive error management
- [Examples](../examples/) - Real-world usage patterns

## See Also

- [`Worker`](../api-reference/worker.md) - For processing enqueued tasks
- [`SQLiteBackend`](../api-reference/backends/sqlite.md) - For SQLite-based task persistence
- [`SyncTaskQueue`](../api-reference/sync.md) - For synchronous task processing
- [`Task`](../api-reference/core.md) - For task data structure
- [`Result`](../api-reference/core.md) - For task result handling