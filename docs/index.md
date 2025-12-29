# sitq Documentation

**Simple Task Queue for Python**

sitq is a lightweight, async-first Python task queue library for running background jobs in small-to-medium services and tools.

```bash
pip install sitq
```

## Quick Example

```python
import asyncio
from sitq import TaskQueue, Worker, SQLiteBackend

async def main():
    backend = SQLiteBackend("tasks.db")
    queue = TaskQueue(backend=backend)
    
    task_id = await queue.enqueue(lambda: "Hello, World!")
    
    worker = Worker(backend)
    await worker.start()
    await asyncio.sleep(1)
    await worker.stop()
    
    result = await queue.get_result(task_id)
    print(result.value)

asyncio.run(main())
```

## Documentation

### [Tutorials](tutorials/index.md)
Learn sitq step-by-step with hands-on lessons. Perfect for getting started.

- [Quickstart](tutorials/quickstart.md) - Get up and running in 5 minutes
- [Delayed Execution](tutorials/delayed-execution.md) - Schedule tasks for later
- [Concurrency Control](tutorials/concurrency.md) - Manage task parallelism
- [Failure Handling](tutorials/failures.md) - Handle errors gracefully
- [Interactive Tutorial](tutorials/interactive-tutorial.ipynb) - Learn by doing in a notebook

### [How-to Guides](how-to/installation.md)
Solve specific problems with practical, goal-oriented guides.

- [Installation](how-to/installation.md) - Install and configure sitq
- [Running Workers](how-to/run-worker.md) - Start and manage workers
- [Getting Results](how-to/get-results.md) - Retrieve task results
- [Handling Failures](how-to/handle-failures.md) - Error handling strategies
- [SQLite Backend](how-to/sqlite-backend.md) - Configure SQLite storage
- [Troubleshooting](how-to/troubleshooting.md) - Common issues and solutions

### [Reference](reference/api/sitq.md)
Technical specifications and API documentation.

- [API Reference](reference/api/sitq.md) - Complete API documentation
- [Error Handling](reference/ERROR_HANDLING.md) - Error types and handling
- [Changelog](reference/changelog.md) - Version history and changes

### [Explanation](explanation/architecture.md)
Understand the design decisions and architecture behind sitq.

- [Architecture](explanation/architecture.md) - System design and components
- [Serialization](explanation/serialization.md) - How tasks/results are serialized
- [Limitations](explanation/limitations.md) - Known limitations and constraints

## Runnable Examples

The [`examples/basic/`](/examples/basic/) directory contains complete, runnable scripts demonstrating all core features:

```bash
# End-to-end workflow
python examples/basic/01_end_to_end.py

# Delayed execution with ETA
python examples/basic/02_eta_delayed_execution.py

# Bounded concurrency control
python examples/basic/03_bounded_concurrency.py

# Failure handling and tracebacks
python examples/basic/04_failures_and_tracebacks.py

# Sync client with async worker
python examples/basic/05_sync_client_with_worker.py
```

## Features

- **Async-first API** with sync wrapper support
- **SQLite backend** for simple, file-based persistence
- **Cloudpickle serialization** for complex Python objects
- **Comprehensive error handling** with detailed context
- **Bounded concurrency** with configurable worker limits
- **Task scheduling** with ETA support
- **Result retrieval** with timeout handling

## Project Links

- [GitHub Repository](https://github.com/legout/sitq)
- [Issue Tracker](https://github.com/legout/sitq/issues)
- [PyPI Package](https://pypi.org/project/sitq/)
