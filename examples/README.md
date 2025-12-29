# sitq Examples

This directory contains runnable examples demonstrating the core features of sitq. Each example is self-contained and can be run independently to learn specific aspects of the library.

## Prerequisites

All examples require:
- Python 3.8+
- sitq installed (see project README for installation instructions)
- SQLite (included in Python standard library)

No external infrastructure (Redis, Postgres, etc.) is required.

## Recommended Learning Path

Follow the numbered examples in order for a complete introduction to sitq:

1. **[01_end_to_end.py](basic/01_end_to_end.py)** - Complete workflow from task enqueueing to result retrieval
   - Demonstrates `TaskQueue` for async task management
   - Shows `Worker` for background task execution
   - Covers `get_result()` and `deserialize_result()` for retrieving task outputs

2. **[02_eta_delayed_execution.py](basic/02_eta_delayed_execution.py)** - Time-based task scheduling
   - Shows how to use `eta` parameter for delayed execution
   - Demonstrates timezone-aware UTC datetime handling
   - Explains task eligibility and execution timing

3. **[03_bounded_concurrency.py](basic/03_bounded_concurrency.py)** - Concurrency control
   - Configures `Worker` with `max_concurrency` limit
   - Demonstrates how bounded concurrency affects task execution
   - Shows task parallelism and resource management

4. **[04_failures_and_tracebacks.py](basic/04_failures_and_tracebacks.py)** - Error handling
   - Shows how task failures are captured and recorded
   - Demonstrates `Result.status` and error information
   - Explains traceback retrieval for debugging

5. **[05_sync_client_with_worker.py](basic/05_sync_client_with_worker.py)** - Synchronous client usage
   - Introduces `SyncTaskQueue` for synchronous task enqueuing
   - Shows sync/async worker coordination
   - Demonstrates shared SQLite backend between sync and async components

## Running the Examples

Each example can be run directly from the command line:

```bash
python examples/basic/01_end_to_end.py
```

All examples:
- Complete within 30 seconds
- Use temporary SQLite databases (cleaned up automatically)
- Exit with status code 0 on success

## Example Design Principles

- **Self-contained**: Each example creates its own temporary database
- **Focused**: Each demonstrates one core feature without overlapping
- **Runnable**: All examples work end-to-end with no external dependencies
- **Robust**: Handle errors gracefully and provide clear output

## Feature Coverage

| Example | Task Enqueue | Worker | Result Retrieval | Delayed (ETA) | Concurrency | Error Handling | Sync Client |
|---------|--------------|--------|------------------|---------------|-------------|----------------|-------------|
| 01_end_to_end.py | ✓ | ✓ | ✓ | - | - | - | - |
| 02_eta_delayed_execution.py | ✓ | ✓ | ✓ | ✓ | - | - | - |
| 03_bounded_concurrency.py | ✓ | ✓ | ✓ | - | ✓ | - | - |
| 04_failures_and_tracebacks.py | ✓ | ✓ | ✓ | - | - | ✓ | - |
| 05_sync_client_with_worker.py | ✓ | ✓ | ✓ | - | - | - | ✓ |

## API Reference

All examples use public sitq APIs:

- `TaskQueue` - Async task queue for enqueuing and retrieving tasks
- `Worker` - Worker for executing tasks from queue
- `SyncTaskQueue` - Synchronous wrapper for TaskQueue
- `SQLiteBackend` - SQLite backend for task persistence
- `Task`, `Result`, `ReservedTask` - Core data structures

For complete API documentation, see the [project docs](../docs/).
