# sitq Documentation

**Simple Task Queue for Python**

sitq is a lightweight, async-first Python task queue library for running background jobs in small-to-medium services and tools.

## Quick Start

```bash
# Install dependencies
pip install sitq
```

Try the runnable examples to see sitq in action:

```bash
# End-to-end workflow
python examples/basic/01_end_to_end.py
```

See [examples/README.md](https://github.com/legout/sitq/tree/main/examples/README.md) for all examples and learning path.

Basic usage:
```python
import asyncio
from sitq import TaskQueue, Worker, SQLiteBackend

async def main():
    # Set up queue and worker
    backend = SQLiteBackend("tasks.db")
    queue = TaskQueue(backend=backend)
    
    # Enqueue a task
    task_id = await queue.enqueue(lambda: "Hello, World!")
    
    # Start worker to process tasks
    worker = Worker(backend=backend)
    await worker.start()
    
    # Wait for task to complete
    await asyncio.sleep(1)
    
    # Stop worker
    await worker.stop()
    
    # Get result
    result = await queue.get_result(task_id)
    if result and result.status == "success":
        value = queue.deserialize_result(result)
        print(f"Result: {value}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Features

- **Async-first API** with sync wrapper support
- **SQLite backend** for simple, file-based persistence
- **Cloudpickle serialization** for complex Python objects
- **Comprehensive error handling** with detailed context
- **Bounded concurrency** with configurable worker limits
- **Task scheduling** with ETA support
- **Result retrieval** with timeout handling

## Documentation

For comprehensive documentation, see our [documentation site](https://sitq.readthedocs.io/).

## Installation

```bash
pip install sitq
```

## Contributing

We welcome contributions! See our [contributing guidelines](https://sitq.readthedocs.io/en/latest/contributing/).