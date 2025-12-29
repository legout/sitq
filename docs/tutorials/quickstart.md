# Quickstart

Get started with sitq in just a few minutes. This tutorial walks you through the complete end-to-end workflow of creating tasks, processing them, and retrieving results.

## Run the Complete Example

The easiest way to learn sitq is to run the end-to-end example:

```bash
python examples/basic/01_end_to_end.py
```

This example demonstrates the complete workflow:
1. Setting up a [`TaskQueue`](../reference/api/sitq.queue.md) with a [`SQLiteBackend`](../reference/api/sitq.backends.sqlite.md)
2. Enqueuing async and sync tasks
3. Starting a [`Worker`](../reference/api/sitq.worker.md) to process tasks
4. Retrieving and deserializing results
5. Clean shutdown

## Understanding the Example

The example code (view it at [`examples/basic/01_end_to_end.py`](https://github.com/legout/sitq/tree/main/examples/basic/01_end_to_end.py)) shows the core sitq pattern:

### 1. Set Up Backend and Queue

```python
from sitq import TaskQueue, Worker, SQLiteBackend

backend = SQLiteBackend("tasks.db")
queue = TaskQueue(backend=backend)
```

The [`SQLiteBackend`](../reference/api/sitq.backends.sqlite.md) stores tasks in a SQLite database. Use `:memory:` for testing or a file path for persistence.

### 2. Enqueue Tasks

```python
task_id = await queue.enqueue(say_hello, "World")
```

Tasks can be async or sync functions. The [`TaskQueue.enqueue()`](../reference/api/sitq.queue.md) method accepts the function and its arguments.

### 3. Start a Worker

```python
worker = Worker(backend)
await worker.start()
```

The [`Worker`](../reference/api/sitq.worker.md) polls the backend for pending tasks and executes them concurrently.

### 4. Get Results

```python
result = await queue.get_result(task_id)
if result and result.status == "success":
    value = queue.deserialize_result(result)
```

[`TaskQueue.get_result()`](../reference/api/sitq.queue.md) retrieves the task result, which includes status, value, and error information.

### 5. Stop the Worker

```python
await worker.stop()
```

Always stop workers to ensure clean shutdown.

## Key Concepts

### TaskQueue

The primary interface for task management:

```python
# Enqueue a task
task_id = await queue.enqueue(function, *args, **kwargs)

# Get a result
result = await queue.get_result(task_id, timeout=30)

# Deserialize result value
value = queue.deserialize_result(result)
```

### Worker

Processes tasks with configurable concurrency:

```python
# Create worker with max 2 concurrent tasks
worker = Worker(backend, max_concurrency=2)

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

## What's Next?

- [Delayed Execution](delayed-execution.md) - Schedule tasks for later execution
- [Concurrency Control](concurrency.md) - Manage task parallelism
- [Failure Handling](failures.md) - Handle errors gracefully
- [Interactive Tutorial](interactive-tutorial.ipynb) - Learn by doing in a notebook

## See Also

- [API Reference](../reference/api/sitq.md) - Complete API documentation
- [How-to Guides](../how-to/installation.md) - Solve specific problems with practical guides
- [Examples](https://github.com/legout/sitq/tree/main/examples/basic/) - More runnable examples