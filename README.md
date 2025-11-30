# Sitq: Simple Task Queue

A lightweight, async-first Python task queue with pluggable back-ends, retry policies, concurrency limits, and distributed locking.

## Key Features

*   **Async First:** Built on Python's `asyncio` for high performance.
*   **Pluggable Backends:** Choose from:
    *   SQLite (for simple, single-file persistence)
    *   PostgreSQL
    *   Redis
    *   NATS (JetStream)
*   **Flexible Workers:**
    *   `AsyncWorker`: For native `async` functions.
    *   `ThreadWorker`: For running synchronous, I/O-bound functions in a thread pool.
    *   `ProcessWorker`: For running synchronous, CPU-bound functions in a process pool.
*   **Serialization:** Supports `cloudpickle` (for complex objects and lambdas) and `json`.
*   **Scheduling:** Enqueue tasks to run at a specific time or after a delay.
*   **Retries:** Automatic, configurable retry policies (e.g., exponential backoff).
*   **Concurrency Control:** Limit the number of tasks running simultaneously.
*   **Sync Wrapper:** A synchronous wrapper (`SyncTaskQueue`) is available for easy integration into legacy codebases.

## Installation

Install the library and its dependencies. The required packages are listed in `pyproject.toml`. You can install them using `pip`:

```bash
pip install "sqlalchemy>=2.0" "aiosqlite>=0.19" "asyncpg>=0.29" "aioredis>=1.3.1,<2" "nats-py>=2.3" "cloudpickle>=3.0" "croniter>=2.0"
pip install .
```

## Examples

### 1. Basic Usage (SQLite Backend)

This example demonstrates the basic workflow: define a task, enqueue it, and run a worker to execute it.

**`main.py`**
```python
import asyncio
from sitq import TaskQueue, Worker, Result
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer

# 1. Define your async task function
async def say_hello(name: str):
    print(f"Hello, {name}")
    return f"Greetings, {name}!"

async def main():
    # 2. Set up the queue with a backend and serializer
    backend = SQLiteBackend("example_queue.db")
    serializer = CloudpickleSerializer()
    queue = TaskQueue(backend, serializer)

    # 3. Enqueue a task and get its ID
    task_id = await queue.enqueue(say_hello, "World")
    print(f"Task {task_id} enqueued.")

    # 4. Start a worker to process the task
    worker = Worker(backend, serializer, concurrency=5)

    # Run the worker for a short period to process the task
    await worker.start()
    await asyncio.sleep(1) # Allow time for the task to be processed
    await worker.stop()

    # 5. Retrieve the result
    result = await queue.get_result(task_id, timeout=5)
    if result and result.is_success():
        print(f"Result received: {result.status}")
        print(f"Task return value: {result.value}")
    else:
        print("Did not receive result in time.")

    # 6. Clean up
    await queue.close()

if __name__ == "__main__":
    asyncio.run(main())
```

**To run this:**
1.  Save the code as `main.py`.
2.  Run `python main.py` from your terminal.

**Expected Output:**
```
Task <uuid> enqueued.
Hello, World
Result received: success
Task return value: Greetings, World!
```

### 2. Using the Redis Backend

To use a different backend, simply swap the `backend` instance.

```python
import asyncio
from sitq import TaskQueue, Worker
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer

# ... (define your task functions)

async def main():
    # Use SQLiteBackend (RedisBackend would be imported similarly when available)
    backend = SQLiteBackend("tasks.db")
    serializer = CloudpickleSerializer()
    queue = TaskQueue(backend, serializer)
    
    # ... rest of the logic is the same
```

### 3. Running a Worker for a CPU-Bound Task

If you have a synchronous, CPU-intensive task, use the `ProcessWorker`.

**`cpu_task_example.py`**
```python
import asyncio
import time
from sitq import TaskQueue, Worker, Result
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer

# A CPU-bound function
def compute_fibonacci(n):
    if n <= 1:
        return n
    else:
        return compute_fibonacci(n-1) + compute_fibonacci(n-2)

async def main():
    backend = SQLiteBackend("cpu_tasks.db")
    serializer = CloudpickleSerializer()
    queue = TaskQueue(backend, serializer)

    # Use Worker with high concurrency for CPU-bound tasks
    worker = Worker(
        backend=backend,
        serializer=serializer,
        concurrency=2  # Run up to 2 CPU-bound tasks in parallel
    )

    await worker.start()

    print("Enqueuing CPU-bound task...")
    task_id = await queue.enqueue(compute_fibonacci, 35)

    result = await queue.get_result(task_id, timeout=20)
    if result and result.is_success():
        print(f"Fibonacci result: {result.value}")
    else:
        print(f"Task failed or timed out. Status: {result.status if result else 'timeout'}")

    await worker.stop()
    await queue.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. Using the Synchronous Wrapper

For non-`async` applications, you can use the `SyncTaskQueue` wrapper.

**`sync_example.py`**
```python
from sitq import SyncTaskQueue, Result
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer

def add(x, y):
    return x + y

# The SyncTaskQueue manages the event loop internally
with SyncTaskQueue(
    backend=SQLiteBackend("sync_queue.db"),
    serializer=CloudpickleSerializer()
) as queue:
    task_id = queue.enqueue(add, 5, 10)
    print(f"Task {task_id} enqueued.")

    # Note: You still need to run an async worker separately
    # to process the tasks from the queue.
```
