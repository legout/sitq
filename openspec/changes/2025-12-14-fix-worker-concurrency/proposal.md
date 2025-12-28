# Change: Fix Worker Concurrency (Bounded Dispatch + Task Tracking)

## Why

The current `Worker` implementation does not reliably enforce `max_concurrency` because it schedules execution tasks before acquiring the concurrency semaphore and does not consistently track the tasks actually running. This can lead to unbounded growth in scheduled work, degraded performance, and shutdown behavior that does not reliably wait for all in-flight tasks.

This change restores the intended bounded concurrency semantics required by `worker-core`.

## What Changes

- Enforce `max_concurrency` by acquiring concurrency permits **before** dispatching execution tasks.
- Track the actual in-flight asyncio tasks created by the worker so `stop()` can reliably await them.
- Remove redundant/double task-wrapping patterns that increase overhead.

## Impact

- Affected specs:
  - `worker-core`
- Affected code (expected):
  - `src/sitq/worker.py`
- **BREAKING**: None intended; this is a correctness/performance fix to match v1 worker semantics.

## Notes / Risks

- Concurrency changes can surface latent race conditions in tests; this change should be validated with integration tests using `SQLiteBackend` and multiple tasks.

