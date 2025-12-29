# Delayed Execution

Schedule tasks for later execution using the ETA (Estimated Time of Arrival) parameter.

## Run the Example

```bash
python examples/basic/02_eta_delayed_execution.py
```

This example demonstrates:
1. Enqueuing tasks with scheduled execution times
2. Using timezone-aware UTC datetimes
3. Observing that tasks execute only after their ETA
4. Retrieving results from delayed tasks

View the full example at [`examples/basic/02_eta_delayed_execution.py`](../../examples/basic/02_eta_delayed_execution.py)

## Scheduling Tasks with ETA

To schedule a task for later execution, pass an `eta` parameter to [`TaskQueue.enqueue()`](../reference/api/sitq.queue.md):

```python
from datetime import datetime, timezone, timedelta
from sitq import TaskQueue, SQLiteBackend

backend = SQLiteBackend("tasks.db")
queue = TaskQueue(backend=backend)

# Schedule task for 5 seconds from now
eta = datetime.now(timezone.utc) + timedelta(seconds=5)
task_id = await queue.enqueue(my_function, "arg1", eta=eta)
```

### Important Requirements

- **Timezone-aware datetimes**: ETA must be timezone-aware. Using UTC is recommended.
- **Future times only**: ETA must be in the future. Past times are treated as immediately eligible.
- **Polling**: Worker must be running and polling for tasks to execute them when they become eligible.

## How It Works

The workflow for delayed execution:

1. **Enqueue with ETA**: Task is stored in the backend with its scheduled time
2. **Worker Polling**: Worker periodically checks for tasks whose ETA has passed
3. **Eligibility Check**: When `current_time >= eta`, task becomes eligible for execution
4. **Execution**: Worker executes the task and stores the result

## Example: Multiple Scheduled Tasks

```python
from datetime import datetime, timezone, timedelta

now = datetime.now(timezone.utc)

# Schedule tasks at different times
eta_1 = now + timedelta(seconds=1)
task_1 = await queue.enqueue(task_func, "First task", eta=eta_1)

eta_2 = now + timedelta(seconds=2)
task_2 = await queue.enqueue(task_func, "Second task", eta=eta_2)

eta_3 = now + timedelta(seconds=3)
task_3 = await queue.enqueue(task_func, "Third task", eta=eta_3)

# Start worker with short poll interval to catch scheduled tasks
worker = Worker(backend, poll_interval=0.5)
await worker.start()

# Wait for tasks to complete
await asyncio.sleep(5)

# Retrieve results
result_1 = await queue.get_result(task_1)
result_2 = await queue.get_result(task_2)
result_3 = await queue.get_result(task_3)
```

## Worker Configuration

For delayed execution, configure the worker's poll interval:

```python
# Poll every 0.5 seconds (default is 1 second)
worker = Worker(backend, poll_interval=0.5)
```

A shorter poll interval means tasks execute closer to their ETA, but increases CPU usage. A longer poll interval reduces CPU usage but may delay execution slightly.

## Common Use Cases

- **Scheduled Jobs**: Run cleanup or maintenance tasks at specific times
- **Rate Limiting**: Delay execution to avoid overwhelming external services
- **Time-dependent Processing**: Process data only after a certain time
- **Batch Processing**: Group tasks to execute together at a scheduled time

## Retrieving Results

Results from delayed tasks work the same as immediate tasks:

```python
result = await queue.get_result(task_id)
if result and result.status == "success":
    value = queue.deserialize_result(result)
    print(f"Result: {value}")
```

## Best Practices

1. **Use UTC timezones**: Avoid timezone confusion by using UTC for all ETAs
2. **Set appropriate poll intervals**: Balance responsiveness with resource usage
3. **Handle worker startup**: Ensure worker is running before tasks become eligible
4. **Check task status**: Use [`TaskQueue.get_result()`](../reference/api/sitq.queue.md) to verify completion
5. **Handle timeouts**: Set reasonable timeouts when retrieving delayed results

## What's Next?

- [Concurrency Control](concurrency.md) - Manage task parallelism
- [Failure Handling](failures.md) - Handle errors gracefully
- [Running Workers](../how-to/run-worker.md) - Configure worker behavior

## See Also

- [`TaskQueue.enqueue()`](../reference/api/sitq.queue.md) - Enqueue tasks with ETA
- [`Worker`](../reference/api/sitq.worker.md) - Worker configuration options
- [Getting Results](../how-to/get-results.md) - Retrieve task results
