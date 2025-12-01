# Workers

Workers are responsible for executing tasks from the queue. sitq provides flexible worker configurations for different use cases.

## Basic Worker Usage

```python
import sitq
import time

# Create a queue and worker
queue = sitq.TaskQueue(backend=sitq.SQLiteBackend(":memory:"))
worker = sitq.Worker(queue)

# Define a task function
def process_data(data):
    """Process some data."""
    time.sleep(0.1)  # Simulate work
    return f"Processed: {data}"

# Enqueue a task
task = sitq.Task(function=process_data, args=["test_data"])
task_id = queue.enqueue(task)

# Process the task
result = worker.process_task(task_id)
print(f"Result: {result.value}")
```

## Worker Lifecycle

### Starting and Stopping Workers

```python
# Create worker
worker = sitq.Worker(queue)

# Start worker (runs continuously)
worker.start()

# Let it run for a while
time.sleep(10)

# Stop worker gracefully
worker.stop()

# Or use context manager
with sitq.Worker(queue) as worker:
    # Worker automatically started
    time.sleep(10)
    # Worker automatically stopped
```

### Continuous Processing

```python
# Worker that processes tasks continuously
worker = sitq.Worker(queue)

# Run for a specific duration
worker.run(duration=60)  # Run for 60 seconds

# Run until interrupted
try:
    worker.run()  # Runs forever
except KeyboardInterrupt:
    print("Worker stopped by user")
```

## Worker Configuration

### Basic Configuration

```python
# Worker with custom settings
worker = sitq.Worker(
    queue=queue,
    poll_interval=1.0,      # Check for tasks every 1 second
    max_tasks=100,          # Process max 100 tasks then stop
    timeout=300.0,          # Task timeout in seconds
    retry_failed=True       # Automatically retry failed tasks
)
```

### Concurrency Settings

```python
# Multi-threaded worker
worker = sitq.Worker(
    queue=queue,
    max_workers=4,          # Use 4 threads
    worker_type="thread"    # Thread-based workers
)

# Process-based worker (for CPU-bound tasks)
worker = sitq.Worker(
    queue=queue,
    max_workers=2,          # Use 2 processes
    worker_type="process"   # Process-based workers
)
```

## Task Processing

### Single Task Processing

```python
# Process a specific task
result = worker.process_task(task_id)

if result.is_success:
    print(f"Task succeeded: {result.value}")
else:
    print(f"Task failed: {result.error}")
```

### Batch Processing

```python
# Process multiple tasks
task_ids = [queue.enqueue(task) for task in tasks]
results = worker.process_tasks(task_ids)

for task_id, result in zip(task_ids, results):
    if result.is_success:
        print(f"Task {task_id}: {result.value}")
    else:
        print(f"Task {task_id} failed: {result.error}")
```

### Automatic Task Discovery

```python
# Worker automatically finds and processes queued tasks
worker = sitq.Worker(queue, poll_interval=0.5)

# Start continuous processing
worker.start()

# Worker will:
# 1. Poll queue for available tasks
# 2. Process tasks in order of priority
# 3. Handle errors and retries
# 4. Continue until stopped
```

## Error Handling

### Task Error Handling

```python
def risky_task(data):
    """Task that might fail."""
    if data == "fail":
        raise ValueError("Intentional failure")
    return f"Success: {data}"

# Worker with error handling
worker = sitq.Worker(
    queue=queue,
    max_retries=3,          # Retry failed tasks up to 3 times
    retry_delay=1.0,        # Wait 1 second between retries
    continue_on_error=True  # Continue processing other tasks
)

# Process task that will fail
task = sitq.Task(function=risky_task, args=["fail"])
task_id = queue.enqueue(task)

result = worker.process_task(task_id)
print(f"Final result: {result.is_error}")
```

### Worker Error Callbacks

```python
def on_task_error(task_id, error, retry_count):
    """Called when a task fails."""
    print(f"Task {task_id} failed (attempt {retry_count}): {error}")

def on_task_success(task_id, result):
    """Called when a task succeeds."""
    print(f"Task {task_id} succeeded: {result}")

# Worker with error callbacks
worker = sitq.Worker(
    queue=queue,
    on_error=on_task_error,
    on_success=on_task_success
)
```

## Performance Optimization

### Worker Pooling

```python
# Create multiple workers for parallel processing
workers = [
    sitq.Worker(queue, worker_id=f"worker_{i}")
    for i in range(4)
]

# Start all workers
for worker in workers:
    worker.start()

# Let them process tasks
time.sleep(60)

# Stop all workers
for worker in workers:
    worker.stop()
```

### Resource Management

```python
# Worker with resource limits
worker = sitq.Worker(
    queue=queue,
    max_memory_mb=1024,     # Limit memory usage
    max_cpu_percent=80.0,   # Limit CPU usage
    graceful_shutdown=30.0   # Graceful shutdown timeout
)
```

## Monitoring and Logging

### Worker Status

```python
# Check worker status
status = worker.get_status()
print(f"Worker running: {status.is_running}")
print(f"Tasks processed: {status.tasks_processed}")
print(f"Tasks failed: {status.tasks_failed}")
print(f"Current task: {status.current_task_id}")
print(f"Uptime: {status.uptime}")
```

### Worker Metrics

```python
# Get detailed metrics
metrics = worker.get_metrics()
print(f"Average task duration: {metrics.avg_task_duration}")
print(f"Tasks per second: {metrics.tasks_per_second}")
print(f"Success rate: {metrics.success_rate}")
print(f"Error rate: {metrics.error_rate}")
```

### Custom Logging

```python
import logging

# Configure worker logging
logging.basicConfig(level=logging.INFO)

# Worker with custom logger
worker = sitq.Worker(
    queue=queue,
    logger=logging.getLogger("my_worker"),
    log_level=logging.INFO,
    log_tasks=True,         # Log each task
    log_errors=True,        # Log errors with stack traces
    log_performance=True     # Log performance metrics
)
```

## Advanced Worker Patterns

### Specialized Workers

```python
# Worker for specific task types
class ImageProcessingWorker(sitq.Worker):
    """Worker specialized for image processing tasks."""
    
    def __init__(self, queue):
        super().__init__(queue)
        self.supported_functions = ["resize_image", "filter_image", "convert_image"]
    
    def should_process_task(self, task):
        """Check if worker should process this task."""
        return task.function.__name__ in self.supported_functions
    
    def process_task(self, task_id):
        """Process only supported tasks."""
        task = self.queue.get_task(task_id)
        if not self.should_process_task(task):
            return sitq.Result(
                is_error=True,
                error="Task type not supported by this worker"
            )
        return super().process_task(task_id)

# Use specialized worker
worker = ImageProcessingWorker(queue)
```

### Worker with Custom Serialization

```python
import pickle

# Worker with custom serialization
worker = sitq.Worker(
    queue=queue,
    serializer=pickle,       # Custom serializer
    deserializer=pickle     # Custom deserializer
)
```

## Best Practices

1. **Choose the right worker type**: Threads for I/O-bound, processes for CPU-bound
2. **Set appropriate timeouts**: Prevent hanging tasks
3. **Handle errors gracefully**: Use retry mechanisms and error callbacks
4. **Monitor worker health**: Track metrics and status
5. **Use resource limits**: Prevent workers from consuming too many resources
6. **Implement graceful shutdown**: Allow workers to finish current tasks

## Next Steps

- [Task Queues Guide](task-queues.md) - Learn about queue management
- [Backends Guide](backends.md) - Explore storage options
- [Error Handling Guide](error-handling.md) - Comprehensive error management
- [Examples](../examples/) - Real-world worker patterns

## See Also

- [`TaskQueue`](../api-reference/queue.md) - For enqueuing tasks to be processed by workers
- [`SQLiteBackend`](../api-reference/backends/sqlite.md) - For SQLite-based task persistence
- [`SyncTaskQueue`](../api-reference/sync.md) - For synchronous task processing
- [`Task`](../api-reference/core.md) - For task data structure
- [`Result`](../api-reference/core.md) - For task result handling