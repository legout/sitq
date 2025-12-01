## Context
sitq v1 needs a single, embedded, file-backed backend that supports async operations and basic multi-worker concurrency. The `SQLiteBackend` will be the only official backend in v1 and must provide durable storage for tasks and results while implementing the at-least-once delivery semantics described in the PRD and SPEC.

The backend is used by `TaskQueue` (for enqueueing and result lookups) and by `Worker` (for reserving tasks and recording outcomes). It must be safe for multiple worker processes on the same host to share a single SQLite database file.

## Goals / Non-Goals
- Goals:
  - Provide an async backend interface with `enqueue`, `reserve`, `mark_success`, `mark_failure`, `get_result`, `connect`, and `close`.
  - Implement `SQLiteBackend` using a single `tasks` table for both pending work and results.
  - Support basic multi-process worker concurrency against one DB file by using SQLite transactions and WAL mode.
  - Preserve at-least-once semantics even under worker crashes.
- Non-Goals:
  - Exactly-once delivery or strong distributed guarantees.
  - Cross-database portability (Postgres/Redis/etc. are future capabilities).
  - Complex migration tooling; v1 only needs table creation on first use.

## Decisions
- Decision: Use a single `tasks` table
  - Store task metadata, payload, timing fields, status, and result columns in one table to keep queries simple and avoid joins.
  - Add indexes on `(status, available_at)` and `task_id` (PRIMARY KEY) to support efficient reservation and lookup.

- Decision: Use SQLite WAL mode for concurrency
  - Enable write-ahead logging (WAL) on connect where supported so multiple worker processes can read and write concurrently to the same database file.
  - Accept that WAL requires a single writer at a time but provides good enough throughput for v1’s small-to-medium workloads.

- Decision: Implement `reserve` via transactional update
  - Use a single transaction per reservation batch:
    - Select up to `max_items` rows with `status = 'pending'` and `available_at <= now`.
    - Mark them `in_progress` and set `started_at` inside the same transaction to avoid multiple workers taking the same task.
  - Prefer an `UPDATE ... WHERE rowid IN (...)` pattern that is compatible with common SQLite versions.

- Decision: Async access via direct SQLite driver
  - Use an async SQLite driver (e.g. `aiosqlite`) with explicit SQL statements instead of a heavy ORM to keep the implementation small and predictable.
  - Keep SQL localized in the backend module so future backends can use different drivers without affecting core logic.

## Risks / Trade-offs
- Risk: Task duplication after crashes
  - A worker may crash after tasks are marked `in_progress` but before `mark_success`/`mark_failure` is called; at-least-once semantics accept that tasks can be retried.
  - Mitigation: Document idempotency requirements clearly and keep the state machine simple (`pending` → `in_progress` → `success`/`failed`).

- Risk: Lock contention with many workers
  - Multiple workers contending for the same SQLite file can cause lock timeouts or reduced throughput.
  - Mitigation: Recommend a small number of worker processes for v1, and provide configuration for `batch_size` and polling behavior in the worker.

- Trade-off: Simple schema vs. flexibility
  - A single table and small status enum are easy to reason about but less flexible than multiple tables for tasks/results/history.
  - This is acceptable for v1 and can be revisited in future versions if richer history or metrics are needed.

## Migration Plan
- v1:
  - On first `connect`, create the `tasks` table if it does not exist.
  - Avoid destructive schema changes once data exists.
- Future:
  - Introduce a simple migration mechanism (versioned schema or migrations table) if new columns or indexes are added in later versions.

## Open Questions
- Should the database path be configurable via environment variables in addition to explicit constructor arguments?
- Do we want to expose any tuning options (busy timeout, pragmas beyond WAL) in the public API, or keep them internal for now?
- How aggressively should we index additional columns (e.g. `available_at` alone) given expected v1 workloads?

