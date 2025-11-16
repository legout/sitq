# Change: Add TaskQueue lifecycle, defaults, and context support

## Why
The current `TaskQueue`, `SyncTaskQueue`, and backend contracts in code do not yet cover all behaviors described in `PRD_v1.md` / `SPEC_v1.md` for v1: there is no default backend or result timeout configuration, no async context manager support on `TaskQueue`, no explicit backend lifecycle hook, and no formal handling of the optional task `context` field. This gap makes it harder to rely on the documented v1 API surface and lifecycle semantics.

## What Changes
- Extend the `task-queue-core` capability to cover the full v1 TaskQueue configuration surface, including optional `backend` / `serializer`, `default_result_timeout`, the optional `context` parameter on `enqueue`, and async context manager methods.
- Introduce a backend lifecycle requirement in `backend-sqlite` that adds an explicit `connect()` step and makes it clear how backends manage connections before use.
- Extend the `backend-sqlite` capability to describe how enqueue/reserve operations populate canonical timing fields (`enqueued_at`, `started_at`, `finished_at`) used by the Result model.
- Extend the `sync-task-queue` capability so that the sync wrapper surfaces `default_result_timeout` semantics consistently with the async TaskQueue.

## Impact
- Affected specs: `task-queue-core`, `backend-sqlite`, `sync-task-queue`
- Affected code: `src/sitq/queue.py`, `src/sitq/result.py`, `src/sitq/backends/base.py`, `src/sitq/backends/sqlite.py`, `src/sitq/sync.py`, related tests under `tests/`

