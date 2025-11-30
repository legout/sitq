## 1. Specification
- [x] 1.1 Update `task-queue-core` spec to document TaskQueue configuration (`backend`, `serializer`, `default_result_timeout`), async context manager behavior, and the optional `context` argument on `enqueue`.
- [x] 1.2 Update `backend-sqlite` spec to add a backend lifecycle requirement (`connect` / `close`) and clarify how `enqueued_at`, `started_at`, and `finished_at` are populated.
- [x] 1.3 Update `sync-task-queue` spec to describe how `default_result_timeout` is exposed and delegated through the synchronous wrapper.

## 2. Implementation
- [x] 2.1 Refactor `TaskQueue` to accept optional `backend` / `serializer`, support `default_result_timeout`, implement `__aenter__` / `__aexit__`, and accept an optional `context` dict on `enqueue`.
- [x] 2.2 Extend the backend protocol in `src/sitq/backends/base.py` with an async `connect()` method and ensure `SQLiteBackend` implements it.
- [x] 2.3 Update `SQLiteBackend` to populate and persist `enqueued_at`, `started_at`, and `finished_at` timestamps in a way that matches the Result model used by the queue.
- [x] 2.4 Wire `default_result_timeout` through both `TaskQueue.get_result` and `SyncTaskQueue.get_result`, ensuring explicit `timeout` arguments take precedence over the default.

## 3. Testing
- [x] 3.1 Extend TaskQueue and SyncTaskQueue tests to cover default backend selection, context manager usage, `default_result_timeout`, and the optional `context` argument.
- [x] 3.2 Extend SQLite backend tests to validate `connect()` behavior and timestamp population (`enqueued_at`, `started_at`, `finished_at`).
- [x] 3.3 Run the full test suite to confirm all updated lifecycle and timeout semantics behave as specified.

