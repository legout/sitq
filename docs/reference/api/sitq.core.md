# sitq.core

Core data structures for sitq.

```{eval-rst}
.. automodule:: sitq.core
```

## Task

```{eval-rst}
.. autoclass:: Task
```

Task data structure for storing function and arguments.

**Attributes:**
- `id` (int): Unique task identifier
- `function` (Callable): Function to execute
- `args` (tuple): Positional arguments
- `kwargs` (dict): Keyword arguments
- `eta` (datetime, optional): Estimated time of arrival
- `status` (str): Task status ("queued", "running", "completed", "failed")
- `created_at` (datetime): Task creation timestamp

## Result

```{eval-rst}
.. autoclass:: Result
```

Result data structure for task execution results.

**Attributes:**
- `task_id` (int): Associated task ID
- `status` (str): Result status ("success", "failed", "pending")
- `value` (bytes): Serialized result value (if success)
- `error` (str, optional): Error message (if failed)
- `traceback` (str, optional): Python traceback (if failed)
- `created_at` (datetime): Result creation timestamp
- `completed_at` (datetime, optional): Task completion timestamp

## ReservedTask

```{eval-rst}
.. autoclass:: ReservedTask
```

Reserved task structure used by workers.

**Attributes:**
- `id` (int): Task identifier
- `function` (Callable): Function to execute
- `args` (tuple): Function arguments
- `kwargs` (dict): Keyword arguments
- `eta` (datetime, optional): Scheduled execution time

## Usage Example

```python
from sitq import TaskQueue, Worker, SQLiteBackend

backend = SQLiteBackend("tasks.db")
queue = TaskQueue(backend=backend)

# Enqueue task
task_id = await queue.enqueue(my_function, "arg")

# Get result
result = await queue.get_result(task_id)

# Check status
if result and result.status == "success":
    value = queue.deserialize_result(result)
    print(f"Result: {value}")
elif result:
    print(f"Error: {result.error}")
```

## See Also

- [`TaskQueue`](sitq.queue.md) - Queue implementation
- [`Worker`](sitq.worker.md) - Worker implementation
- [`Backend`](sitq.backends.base.md) - Backend interface
