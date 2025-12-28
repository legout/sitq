# Sitq: Simple Task Queue

A lightweight, async-first Python task queue with pluggable backends and comprehensive error handling.

## Key Features

*   **Async First:** Built on Python's `asyncio` for high performance.
*   **Pluggable Backends:** Currently supports:
    *   SQLite (for simple, single-file persistence)
    *   Additional backends (PostgreSQL, Redis, NATS) planned for future releases
*   **Worker Support:** Single `Worker` class that handles both async and sync functions:
    *   Executes async functions natively
    *   Executes sync functions in thread pool automatically
    *   Configurable concurrency and polling intervals
*   **Serialization:** Built-in `CloudpickleSerializer` for complex objects and lambdas.
*   **Scheduling:** Enqueue tasks to run at specific times with ETA support.
*   **Error Handling:** Comprehensive exception hierarchy with detailed error context.
*   **Sync Wrapper:** `SyncTaskQueue` available for integration into legacy codebases.

## Installation

Install sitq and its dependencies:

```bash
# Install dependencies and package
pip install .
```

For development:
```bash
# Clone and install in development mode
git clone <repository>
cd sitq
pip install -e .
```

## Examples

### 1. API Structure Demo

See the `examples/basic/` directory for runnable examples that demonstrate the current sitq API:

```bash
# Run the API structure demo
python examples/basic/api_demo.py
```

This shows the available API surface and confirms all components import correctly.

### 2. Basic Usage Pattern

The current sitq API follows this pattern:

```python
import asyncio
from sitq import TaskQueue, Worker, SQLiteBackend

async def my_task(name: str) -> str:
    """Example task function."""
    await asyncio.sleep(0.1)  # Simulate work
    return f"Hello, {name}!"

async def main():
    # Set up backend and queue
    backend = SQLiteBackend("tasks.db")
    queue = TaskQueue(backend=backend)
    
    # Enqueue a task
    task_id = await queue.enqueue(my_task, "World")
    
    # Start worker to process tasks
    worker = Worker(backend, max_concurrency=2)
    
    try:
        # Start worker in background
        worker_task = asyncio.create_task(worker.start())
        
        # Give worker time to process
        await asyncio.sleep(2)
        
        # Get result
        result = await queue.get_result(task_id, timeout=5)
        if result and result.status == "success":
            value = queue.deserialize_result(result)
            print(f"Result: {value}")
        
    finally:
        await worker.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Current Implementation Status

**✅ Working Components:**
- `TaskQueue` - Async task queue for enqueuing/retrieving tasks
- `Worker` - Unified worker for both async and sync functions  
- `SQLiteBackend` - SQLite backend for task persistence
- `CloudpickleSerializer` - Default serialization
- Core exception classes and validation

**🔧 Under Development:**
- Full end-to-end task processing (backend fixes needed)
- Additional backends (PostgreSQL, Redis, NATS)
- Advanced retry policies and scheduling features

### 4. Running Examples

```bash
# Basic API verification
python examples/basic/api_demo.py

# When backend issues are resolved, try:
python examples/basic/quickstart_simple.py
```

**Note:** The current implementation focuses on core functionality. Some advanced features shown in planning documentation are still under development.
