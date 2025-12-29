# Sitq: Simple Task Queue

A lightweight, async-first Python task queue with pluggable backends and comprehensive error handling.

## Key Features

*   **Async First:** Built on Python's `asyncio` for high performance.
*   **Pluggable Backends:** Currently supports SQLite for simple, single-file persistence.
*   **Worker Support:** Single `Worker` class that handles both async and sync functions:
    *   Executes async functions natively
    *   Executes sync functions in thread pool automatically
    *   Configurable concurrency and polling intervals
*   **Serialization:** Built-in `CloudpickleSerializer` for complex objects and lambdas.
*   **Scheduling:** Enqueue tasks to run at specific times with ETA support.
*   **Error Handling:** Comprehensive exception hierarchy with detailed error context.
*   **Sync Wrapper:** `SyncTaskQueue` available for integration into legacy codebases.

## v1 Supported Features

### Core Components
-   **TaskQueue** - Async task queue for enqueuing/retrieving tasks
-   **Worker** - Unified worker for processing both async and sync functions
-   **SQLiteBackend** - SQLite backend for task persistence
-   **CloudpickleSerializer** - Default serialization for complex Python objects
-   **SyncTaskQueue** - Synchronous wrapper for non-async contexts

### Capabilities
-   Async and sync function execution (automatic detection)
-   Configurable worker concurrency
-   Task results persistence
-   Error tracking with tracebacks
-   ETA-based delayed execution
-   Comprehensive validation
-   Timeout handling with `None` return on timeout

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

See `examples/basic/` directory for runnable examples that demonstrate the current sitq API:

```bash
# Run API structure demo
python examples/basic/api_demo.py
```

This shows:
- Available API surface (TaskQueue, Worker, SQLiteBackend)
- How to import and use each component
- Current v1 capabilities

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
    await backend.connect()
    queue = TaskQueue(backend=backend)
    
    # Enqueue a task
    task_id = await queue.enqueue(my_task, "World")
    
    # Start worker to process tasks
    worker = Worker(backend, max_concurrency=2)
    worker_task = asyncio.create_task(worker.start())
    
    # Get result
    result = await queue.get_result(task_id, timeout=5)
    if result and result.status == "success":
        value = queue.deserialize_result(result)
        print(f"Result: {value}")
    
    # Cleanup
    await worker.stop()
    await worker_task
    await backend.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. End-to-End Workflow

For a complete demonstration of enqueue → worker processes → get_result:

```bash
python example_end_to_end.py
```

This script shows:
- Enqueuing multiple tasks
- Worker processing with concurrency control
- Retrieving results with timeout handling
- Error handling for failed tasks
- Proper resource cleanup

### 4. Sync Context Usage

For integrating into synchronous codebases:

```python
from sitq import SyncTaskQueue, SQLiteBackend

def main():
    # SyncTaskQueue manages its own event loop
    with SyncTaskQueue(SQLiteBackend("tasks.db")) as queue:
        task_id = queue.enqueue(my_task, "World")
        result = queue.get_result(task_id, timeout=5)
        print(f"Result: {result}")

if __name__ == "__main__":
    main()
```

**Important:** SyncTaskQueue cannot be used inside an existing event loop. Use TaskQueue directly in async contexts (FastAPI, async handlers).

### 5. Current Implementation Status

**✅ Working Components:**
- TaskQueue (async task queue)
- Worker (handles both async and sync functions)
- SQLiteBackend (task persistence with automatic schema migration)
- CloudpickleSerializer (serialization)
- Core exception classes and validation
- SyncTaskQueue (sync wrapper for non-async contexts)

**🔧 Under Development:**
- Additional backends (PostgreSQL, Redis, NATS)
- Advanced retry policies and scheduling features

See planning documentation for roadmap of future features.

## Documentation

Full documentation is available in the `docs/` directory:

-   **User Guide:** Detailed usage examples and best practices
-   **Architecture:** System design and component interactions
-   **Error Handling:** Exception hierarchy and error scenarios
-   **Testing:** How to run and extend the test suite

Run local docs:
```bash
# Serve documentation
mkdocs serve docs/

# Or build
mkdocs build docs/
```

## Testing

The test suite is organized by type:

```bash
# Run all tests (unit + integration)
pytest

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run performance tests (explicitly)
pytest -m performance

# Run validation tests
pytest tests/validation/
```

See `tests/README.md` for complete test documentation.

## Development

### Project Structure

```
sitq/
├── src/sitq/          # Core library code
│   ├── queue.py         # TaskQueue implementation
│   ├── worker.py         # Worker implementation
│   ├── backends/        # Backend implementations
│   │   └── sqlite.py   # SQLite backend
│   ├── serialization.py  # Serialization logic
│   ├── sync.py          # SyncTaskQueue wrapper
│   ├── core.py           # Core data structures
│   ├── exceptions.py     # Exception hierarchy
│   └── validation.py     # Input validation
├── tests/              # Test suite
│   ├── unit/           # Unit tests
│   ├── integration/      # Integration tests
│   ├── performance/      # Performance benchmarks
│   └── validation/      # Documentation tests
├── examples/            # Runnable examples
│   └── basic/          # Basic usage examples
├── docs/               # Documentation
└── openspec/            # OpenSpec change proposals
```

### Contributing

We welcome contributions! Areas of interest:

- Additional backend implementations (PostgreSQL, Redis, NATS)
- Performance optimizations
- Enhanced scheduling features
- Improved documentation
- Additional test coverage

Please see the OpenSpec proposals in `openspec/` for guidelines on contributing larger features.

## License

[Add your license here]

## Support

- **Documentation:** See `docs/` directory
- **Examples:** See `examples/` directory
- **Issues:** Report issues via GitHub Issues
- **Planning:** See `openspec/` for roadmap and proposed changes
