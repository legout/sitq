# sitq.sync

Synchronous wrapper for task queue operations.

```{eval-rst}
.. automodule:: sitq.sync
```

## SyncTaskQueue

```{eval-rst}
.. autoclass:: SyncTaskQueue
```

Synchronous wrapper around [`TaskQueue`](sitq.queue.md) for non-async workflows.

### Methods

#### `__init__(backend, serializer=None)`

Initialize sync task queue.

**Parameters:**
- `backend` ([`Backend`](sitq.backends.base.md)): Backend instance for task storage
- `serializer` ([`Serializer`](sitq.serialization.md), optional): Serializer instance. Defaults to [`CloudpickleSerializer`](sitq.serialization.md)

**Example:**
```python
from sitq import SyncTaskQueue, SQLiteBackend

backend = SQLiteBackend("tasks.db")
queue = SyncTaskQueue(backend=backend)
```

#### `enqueue(function, *args, eta=None, **kwargs)`

Enqueue a task (synchronous method).

**Parameters:**
- `function` (Callable): Function to execute
- `*args`: Positional arguments for function
- `eta` (datetime, optional): Estimated time of arrival for delayed execution. Must be timezone-aware (UTC recommended)
- `**kwargs`: Keyword arguments for function

**Returns:**
- `str`: Task ID

**Example:**
```python
# Enqueue task
task_id = queue.enqueue(my_function, "arg1", "arg2")

# Task with keyword arguments
task_id = queue.enqueue(my_function, arg1, kwarg="value")

# Delayed execution
from datetime import datetime, timezone, timedelta
eta = datetime.now(timezone.utc) + timedelta(seconds=30)
task_id = queue.enqueue(my_function, arg, eta=eta)
```

#### `get_result(task_id, timeout=None)`

Retrieve task result (synchronous method).

**Parameters:**
- `task_id` (str): Task identifier
- `timeout` (float, optional): Maximum wait time in seconds

**Returns:**
- [`Result`](sitq.core.md) or `None`: Task result, or None if task not found

**Example:**
```python
result = queue.get_result(task_id)

if result and result.status == "success":
    value = result.value  # Already deserialized in sync wrapper
    print(f"Result: {value}")
elif result:
    print(f"Error: {result.error}")
else:
    print("Task not found")
```

#### `__enter__()`, `__exit__()`

Context manager support for automatic resource cleanup.

**Example:**
```python
with SyncTaskQueue(backend=backend) as queue:
    task_id = queue.enqueue(my_function, "arg")
    result = queue.get_result(task_id)
    # Queue cleaned up automatically
```

## Usage Example

```python
from sitq import SyncTaskQueue, SQLiteBackend, Worker

# Setup sync queue
backend = SQLiteBackend("tasks.db")
queue = SyncTaskQueue(backend=backend)

# Use synchronous API
task_id = queue.enqueue(process_data, data)
result = queue.get_result(task_id)

if result and result.status == "success":
    print(f"Success: {result.value}")
```

## When to Use SyncTaskQueue

Use [`SyncTaskQueue`](sitq.sync.md) when:
- Working in synchronous code that can't be async
- Migrating from sync to async systems
- Needing simpler API without async/await
- Building CLI tools or scripts

### Advantages

- Simpler API (no async/await)
- Easier integration with sync code
- Less complex error handling
- Direct result access (no deserialization needed)

### Disadvantages

- Blocking operations
- No concurrent task processing
- Lower throughput than async version
- Limited to single-threaded execution

## Comparison with Async

```python
# Async version (recommended)
from sitq import TaskQueue

async def async_workflow():
    backend = SQLiteBackend("tasks.db")
    queue = TaskQueue(backend=backend)
    
    task_id = await queue.enqueue(my_function, "arg")
    result = await queue.get_result(task_id)
    
    if result and result.status == "success":
        value = queue.deserialize_result(result)
        print(f"Result: {value}")

# Sync version (for sync-only code)
from sitq import SyncTaskQueue

def sync_workflow():
    backend = SQLiteBackend("tasks.db")
    queue = SyncTaskQueue(backend=backend)
    
    task_id = queue.enqueue(my_function, "arg")
    result = queue.get_result(task_id)
    
    if result and result.status == "success":
        value = result.value  # Already deserialized
        print(f"Result: {value}")

# Run sync workflow
sync_workflow()
```

## See Also

- [`TaskQueue`](sitq.queue.md) - Async queue implementation
- [`Worker`](sitq.worker.md) - Worker for task execution
- [`Result`](sitq.core.md) - Result structure
