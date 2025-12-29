# sitq.worker

Worker implementation for executing tasks.

```{eval-rst}
.. automodule:: sitq.worker
```

## Worker

```{eval-rst}
.. autoclass:: Worker
```

### Methods

#### `__init__(backend, serializer=None, max_concurrency=1, poll_interval=1.0)`

Initialize worker.

**Parameters:**
- `backend` ([`Backend`](sitq.backends.base.md)): Backend instance for task reservation and result storage
- `serializer` ([`Serializer`](sitq.serialization.md), optional): Serializer instance. Defaults to [`CloudpickleSerializer`](sitq.serialization.md)
- `max_concurrency` (int, default=1): Maximum number of tasks to execute concurrently (range: 1-1000)
- `poll_interval` (float, default=1.0): Seconds between polling attempts when no tasks available

**Example:**
```python
from sitq import Worker, SQLiteBackend

backend = SQLiteBackend("tasks.db")

# Default configuration
worker = Worker(backend)

# Custom concurrency
worker = Worker(backend, max_concurrency=4)

# Custom polling
worker = Worker(backend, poll_interval=0.5)
```

#### `async start()`

Start worker and begin processing tasks.

**Example:**
```python
worker_task = asyncio.create_task(worker.start())

# Let worker process tasks
await asyncio.sleep(10)

# Worker is now running and processing tasks
```

#### `async stop()`

Stop worker gracefully.

Waits for currently running tasks to complete before stopping.

**Example:**
```python
try:
    worker_task = asyncio.create_task(worker.start())
    await asyncio.sleep(10)
finally:
    await worker.stop()
```

## Attributes

#### `backend`

Backend instance used by worker.

**Type:** [`Backend`](sitq.backends.base.md)

#### `serializer`

Serializer instance used by worker.

**Type:** [`Serializer`](sitq.serialization.md)

#### `max_concurrency`

Maximum number of concurrent tasks.

**Type:** int

#### `poll_interval`

Seconds between polling attempts.

**Type:** float

#### `_running` (protected)

Whether worker is currently running.

**Type:** bool

## Usage Patterns

### Basic Usage

```python
from sitq import Worker, SQLiteBackend
import asyncio

async def main():
    backend = SQLiteBackend("tasks.db")
    queue = TaskQueue(backend=backend)
    
    # Enqueue task
    task_id = await queue.enqueue(my_function, "arg")
    
    # Start worker
    worker = Worker(backend)
    worker_task = asyncio.create_task(worker.start())
    
    # Wait for processing
    await asyncio.sleep(2)
    
    # Stop worker
    await worker.stop()
    
    # Get result
    result = await queue.get_result(task_id)
    if result and result.status == "success":
        value = queue.deserialize_result(result)
        print(f"Result: {value}")

asyncio.run(main())
```

### Concurrency Control

```python
# Process at most 4 tasks concurrently
worker = Worker(backend, max_concurrency=4)
```

### Multiple Workers

```python
workers = []
for i in range(4):
    worker = Worker(backend, max_concurrency=2)
    workers.append(worker)

# Start all workers
worker_tasks = []
for worker in workers:
    task = asyncio.create_task(worker.start())
    worker_tasks.append(task)

# Wait for tasks to complete
await asyncio.sleep(60)

# Stop all workers
for worker in workers:
    await worker.stop()

await asyncio.gather(*worker_tasks, return_exceptions=True)
```

## See Also

- [`TaskQueue`](sitq.queue.md) - Queue for task management
- [`Backend`](sitq.backends.base.md) - Backend interface
- [`Serializer`](sitq.serialization.md) - Serialization interface
- [`Result`](sitq.core.md) - Result structure
