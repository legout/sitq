# Concurrency Control

Control task parallelism with bounded concurrency limits to prevent resource exhaustion.

## Run the Example

```bash
python examples/basic/03_bounded_concurrency.py
```

This example demonstrates:
1. Configuring [`Worker`](../reference/api/sitq.worker.md) with `max_concurrency` limit
2. Observing how bounded concurrency affects task execution timing
3. Verifying that tasks execute in parallel up to the limit
4. Understanding resource management with controlled parallelism

View the full example at [`examples/basic/03_bounded_concurrency.py`](/examples/basic/03_bounded_concurrency.py)

## Setting Concurrency Limits

Control the maximum number of tasks that can execute simultaneously by setting `max_concurrency`:

```python
from sitq import Worker, SQLiteBackend

backend = SQLiteBackend("tasks.db")

# Execute at most 2 tasks concurrently
worker = Worker(backend, max_concurrency=2)

# Execute at most 10 tasks concurrently
worker = Worker(backend, max_concurrency=10)
```

## How It Works

The bounded concurrency workflow:

1. **Task Submission**: Tasks are enqueued normally
2. **Polling**: Worker polls for pending tasks
3. **Concurrency Check**: Worker checks if current running tasks < `max_concurrency`
4. **Execution**: If under limit, worker starts task; otherwise, task waits in queue
5. **Slot Release**: When a task completes, a slot becomes available for the next task

## Example: Bounded Concurrency

```python
from sitq import TaskQueue, Worker, SQLiteBackend

backend = SQLiteBackend("tasks.db")
queue = TaskQueue(backend=backend)

# Enqueue 5 tasks
for i in range(5):
    await queue.enqueue(slow_task, i)

# Create worker with max_concurrency=2
worker = Worker(backend, max_concurrency=2)

await worker.start()

# Tasks 1 and 2 start immediately
# Tasks 3, 4, and 5 wait in queue
# As tasks complete, waiting tasks start
```

## Choosing the Right Concurrency Limit

The optimal `max_concurrency` depends on your tasks and resources:

### I/O-Bound Tasks
- **High concurrency**: Use limits like 10-100
- Tasks spend most time waiting (e.g., HTTP requests, database queries)
- High concurrency improves throughput

### CPU-Bound Tasks
- **Low concurrency**: Use limits like 1-4
- Tasks spend most time computing (e.g., data processing, image conversion)
- Limit to number of CPU cores to avoid context switching overhead

### Mixed Workloads
- **Medium concurrency**: Use limits like 4-8
- Balance between I/O and CPU operations
- Monitor and adjust based on performance

```python
# I/O-bound task
async def fetch_url(url: str) -> str:
    response = await aiohttp.get(url)
    return await response.text()

# Can handle high concurrency
worker = Worker(backend, max_concurrency=50)
```

```python
# CPU-bound task
async def process_image(image_data: bytes) -> bytes:
    result = heavy_computation(image_data)
    return result

# Limited concurrency prevents CPU overload
worker = Worker(backend, max_concurrency=4)
```

## Concurrency Analysis

The example includes execution timeline analysis to verify concurrency behavior:

```python
# With max_concurrency=2 and 5 tasks:
# - Tasks 1 & 2 run concurrently (0.0s - 0.5s)
# - Tasks 3 & 4 run concurrently (0.5s - 1.0s)
# - Task 5 runs alone (1.0s - 1.5s)
# Total time: ~1.5s (vs 0.5s with unlimited concurrency)
```

## Resource Management

Bounded concurrency prevents resource exhaustion by:

- **Memory Limits**: Prevents running too many memory-intensive tasks
- **Database Connections**: Limits concurrent database queries
- **API Rate Limits**: Controls request rate to external services
- **CPU Usage**: Avoids overwhelming the processor

```python
# Prevent overwhelming external API
worker = Worker(backend, max_concurrency=5)
```

## Best Practices

1. **Monitor Resource Usage**: Adjust limits based on actual resource consumption
2. **Test Under Load**: Verify performance at your expected task volume
3. **Consider Task Duration**: Longer-running tasks may need lower concurrency
4. **Use Separate Workers**: Create different workers for different task types
5. **Document Limits**: Document chosen concurrency limits and rationale

## Advanced: Multiple Workers

For more control, run multiple workers with different limits:

```python
# High-concurrency worker for I/O tasks
io_worker = Worker(backend, max_concurrency=50)
await io_worker.start()

# Low-concurrency worker for CPU tasks
cpu_worker = Worker(backend, max_concurrency=4)
await cpu_worker.start()
```

## What's Next?

- [Failure Handling](failures.md) - Handle errors gracefully
- [Delayed Execution](delayed-execution.md) - Schedule tasks for later
- [Running Workers](../how-to/run-worker.md) - Advanced worker configuration

## See Also

- [`Worker`](../reference/api/sitq.worker.md) - Worker initialization and configuration
- [Performance](../how-to/performance.md) - Performance optimization
