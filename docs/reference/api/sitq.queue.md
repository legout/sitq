# sitq.queue

Task queue implementation for managing task lifecycle.

```{eval-rst}
.. automodule:: sitq.queue
```

## TaskQueue

```{eval-rst}
.. autoclass:: TaskQueue
```

### Methods

#### `__init__(backend, serializer=None)`

Initialize task queue.

**Parameters:**
- `backend` ([`Backend`](sitq.backends.base.md)): Backend instance for task storage
- `serializer` ([`Serializer`](sitq.serialization.md), optional): Serializer instance. Defaults to [`CloudpickleSerializer`](sitq.serialization.md)

**Example:**
```python
from sitq import TaskQueue, SQLiteBackend

backend = SQLiteBackend("tasks.db")
queue = TaskQueue(backend=backend)
```

#### `async enqueue(function, *args, eta=None, **kwargs)`

Enqueue a task for execution.

**Parameters:**
- `function` (Callable): Function to execute
- `*args`: Positional arguments for function
- `eta` (datetime, optional): Estimated time of arrival for delayed execution. Must be timezone-aware (UTC recommended)
- `**kwargs`: Keyword arguments for function

**Returns:**
- `str`: Task ID

**Example:**
```python
# Simple task
task_id = await queue.enqueue(my_function, "arg1", "arg2")

# Task with keyword arguments
task_id = await queue.enqueue(my_function, arg1, kwarg="value")

# Delayed execution
from datetime import datetime, timezone, timedelta
eta = datetime.now(timezone.utc) + timedelta(seconds=30)
task_id = await queue.enqueue(my_function, arg, eta=eta)
```

#### `async get_result(task_id, timeout=None)`

Retrieve task result.

**Parameters:**
- `task_id` (str): Task identifier
- `timeout` (float, optional): Maximum wait time in seconds. Raises `TimeoutError` if exceeded

**Returns:**
- [`Result`](sitq.core.md) or `None`: Task result, or None if task not found

**Example:**
```python
result = await queue.get_result(task_id)

if result and result.status == "success":
    value = queue.deserialize_result(result)
    print(f"Result: {value}")
elif result:
    print(f"Error: {result.error}")
else:
    print("Task not found")
```

#### `deserialize_result(result)`

Deserialize task result value.

**Parameters:**
- `result` ([`Result`](sitq.core.md)): Result object with `status == "success"`

**Returns:**
- Deserialized Python object

**Example:**
```python
result = await queue.get_result(task_id)
if result and result.status == "success":
    value = queue.deserialize_result(result)
```

#### `async __aenter__()`, `async __aexit__()`

Async context manager support.

**Example:**
```python
async with TaskQueue(backend=backend) as queue:
    task_id = await queue.enqueue(my_function)
    result = await queue.get_result(task_id)
```

## See Also

- [`Task`](sitq.core.md) - Task structure
- [`Result`](sitq.core.md) - Result structure
- [`Backend`](sitq.backends.base.md) - Backend interface
- [`Worker`](sitq.worker.md) - Worker implementation
