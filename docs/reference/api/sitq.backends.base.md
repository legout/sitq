# sitq.backends.base

Backend base class for task storage.

```{eval-rst}
.. automodule:: sitq.backends.base
```

## Backend

```{eval-rst}
.. autoclass:: Backend
```

Abstract base class for implementing custom backends.

### Abstract Methods

#### `async enqueue_task(task, function, args, kwargs)`

Store a task in the backend.

**Parameters:**
- `task` ([`Task`](sitq.core.md)): Task to store
- `function` (Callable): Function to execute
- `args` (tuple): Positional arguments
- `kwargs` (dict): Keyword arguments

**Raises:**
- [`BackendError`](sitq.exceptions.md): If task cannot be stored

#### `async reserve_task(worker_id, max_tasks=1)`

Reserve tasks for execution by a worker.

**Parameters:**
- `worker_id` (str): Worker identifier
- `max_tasks` (int, default=1): Maximum tasks to reserve

**Returns:**
- `List[[`ReservedTask`](sitq.core.md)]: List of reserved tasks

#### `async get_task(task_id)`

Retrieve a task by ID.

**Parameters:**
- `task_id` (str): Task identifier

**Returns:**
- [`Task`](sitq.core.md) or `None`: Task object, or None if not found

#### `async update_task_status(task_id, status)`

Update task status.

**Parameters:**
- `task_id` (str): Task identifier
- `status` (str): New status ("queued", "running", "completed", "failed")

#### `async store_result(task_id, result)`

Store task result.

**Parameters:**
- `task_id` (str): Task identifier
- `result` ([`Result`](sitq.core.md)): Result to store

#### `async get_result(task_id)`

Retrieve task result.

**Parameters:**
- `task_id` (str): Task identifier

**Returns:**
- [`Result`](sitq.core.md) or `None`: Result object, or None if not found

## Implementing a Custom Backend

```python
from abc import ABC, abstractmethod
from sitq.backends.base import Backend
from sitq.core import Task, Result
from typing import Optional, List
import asyncio

class MyBackend(Backend):
    """Custom backend implementation."""
    
    async def enqueue_task(self, task: Task, function, args, kwargs):
        """Store task in custom storage."""
        # Your implementation
        pass
    
    async def reserve_task(self, worker_id: str, max_tasks: int = 1) -> List[ReservedTask]:
        """Reserve tasks for worker."""
        # Your implementation
        return []
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        # Your implementation
        return None
    
    async def update_task_status(self, task_id: str, status: str) -> None:
        """Update task status."""
        # Your implementation
        pass
    
    async def store_result(self, task_id: str, result: Result) -> None:
        """Store task result."""
        # Your implementation
        pass
    
    async def get_result(self, task_id: str) -> Optional[Result]:
        """Get task result."""
        # Your implementation
        return None
```

## See Also

- [`SQLiteBackend`](sitq.backends.sqlite.md) - SQLite backend implementation
- [`Task`](sitq.core.md) - Task structure
- [`Result`](sitq.core.md) - Result structure
- [`BackendError`](sitq.exceptions.md) - Backend exceptions
