# sitq.backends.sqlite

SQLite backend implementation for task storage.

```{eval-rst}
.. automodule:: sitq.backends.sqlite
```

## SQLiteBackend

```{eval-rst}
.. autoclass:: SQLiteBackend
```

SQLite backend for task persistence and result storage.

### Methods

#### `__init__(db_path)`

Initialize SQLite backend.

**Parameters:**
- `db_path` (str): Path to SQLite database file. Use `":memory:"` for in-memory database

**Example:**
```python
from sitq.backends.sqlite import SQLiteBackend

# File-based database (persistent)
backend = SQLiteBackend("tasks.db")

# In-memory database (ephemeral)
backend = SQLiteBackend(":memory:")

# With absolute path
backend = SQLiteBackend("/full/path/to/tasks.db")

# With Path object
from pathlib import Path
backend = SQLiteBackend(Path.cwd() / "data" / "tasks.db")
```

## Usage Example

```python
from sitq import TaskQueue, Worker, SQLiteBackend
import asyncio

# Create SQLite backend
backend = SQLiteBackend("tasks.db")

# Use with task queue
queue = TaskQueue(backend=backend)

# Use with worker
worker = Worker(backend)

# Enqueue and process tasks
async def main():
    task_id = await queue.enqueue(my_function, "arg")
    
    worker_task = asyncio.create_task(worker.start())
    await asyncio.sleep(2)
    await worker.stop()
    
    result = await queue.get_result(task_id)
    if result and result.status == "success":
        value = queue.deserialize_result(result)
        print(f"Result: {value}")

asyncio.run(main())
```

## Database Schema

Backend automatically creates SQLite tables:

### `tasks` table

Stores task definitions:
- `id` (INTEGER PRIMARY KEY): Task identifier
- `function` (BLOB): Serialized function
- `args` (BLOB): Serialized arguments
- `kwargs` (BLOB): Serialized keyword arguments
- `eta` (DATETIME): Estimated time of arrival (nullable)
- `status` (TEXT): Task status ("queued", "running", "completed", "failed")
- `created_at` (DATETIME): Task creation timestamp
- `worker_id` (TEXT, nullable): Worker that reserved task

### `results` table

Stores task results:
- `task_id` (INTEGER PRIMARY KEY): Associated task ID
- `status` (TEXT): Result status ("success", "failed")
- `value` (BLOB, nullable): Serialized result value
- `error` (TEXT, nullable): Error message
- `traceback` (TEXT, nullable): Python traceback
- `created_at` (DATETIME): Result creation timestamp
- `completed_at` (DATETIME, nullable): Task completion timestamp

## Performance Considerations

### In-Memory vs File-Based

```python
# In-memory (faster, no persistence)
backend = SQLiteBackend(":memory:")

# File-based (persistent, slower)
backend = SQLiteBackend("tasks.db")
```

**Trade-offs:**
- **In-memory**: Faster, no disk I/O, data lost on restart
- **File-based**: Slower, persistent, survives restarts

### Connection Management

Backend manages SQLite connections automatically. Multiple [`TaskQueue`](sitq.queue.md) or [`Worker`](sitq.worker.md) instances can share the same backend.

## Best Practices

1. **Use absolute paths** for file-based databases to avoid ambiguity
2. **Use `:memory:`** for testing and development
3. **Enable WAL mode** for better concurrency with multiple workers (requires manual SQLite configuration)
4. **Close connections** by using context managers
5. **Back up databases** regularly for production use

## See Also

- [`Backend`](sitq.backends.base.md) - Backend base class
- [`TaskQueue`](sitq.queue.md) - Queue implementation
- [`Worker`](sitq.worker.md) - Worker implementation
- [SQLite Backend Guide](../../how-to/sqlite-backend.md) - Backend configuration and tuning
