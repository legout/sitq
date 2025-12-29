# sitq

Simple Task Queue for Python.

```{eval-rst}
.. automodule:: sitq
```

## Core Components

- [`TaskQueue`](sitq.queue.md) - Async queue for task management
- [`Worker`](sitq.worker.md) - Async worker for task execution
- [`SyncTaskQueue`](sitq.sync.md) - Sync wrapper for task queue
- [`Task`](sitq.core.md) - Task data structure
- [`Result`](sitq.core.md) - Result data structure
- [`ReservedTask`](sitq.core.md) - Reserved task structure

## Backends

- [`Backend`](sitq.backends.base.md) - Backend base class
- [`SQLiteBackend`](sitq.backends.sqlite.md) - SQLite backend implementation

## Serialization

- [`Serializer`](sitq.serialization.md) - Serializer interface
- [`CloudpickleSerializer`](sitq.serialization.md) - Cloudpickle implementation

## Exceptions

- [`SitqError`](sitq.exceptions.md) - Base exception class
- [`TaskQueueError`](sitq.exceptions.md) - Task queue errors
- [`BackendError`](sitq.exceptions.md) - Backend errors
- [`WorkerError`](sitq.exceptions.md) - Worker errors
- [`ValidationError`](sitq.exceptions.md) - Validation errors
- [`SerializationError`](sitq.exceptions.md) - Serialization errors
- [`ConnectionError`](sitq.exceptions.md) - Connection errors
- [`TaskExecutionError`](sitq.exceptions.md) - Task execution errors
- [`TimeoutError`](sitq.exceptions.md) - Timeout errors
- [`ResourceExhaustionError`](sitq.exceptions.md) - Resource exhaustion errors
- [`ConfigurationError`](sitq.exceptions.md) - Configuration errors
- [`SyncTaskQueueError`](sitq.exceptions.md) - Sync task queue errors

## Validation

- [`validate`](sitq.validation.md) - Validation function
- [`ValidationBuilder`](sitq.validation.md) - Validation builder
