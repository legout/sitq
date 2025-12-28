# Change: Add core async TaskQueue and Result model

## Why
sitq v1 needs a minimal async-first queue API and canonical result model as the foundation for workers, backends, and sync wrappers.

## What Changes
- Introduce a `task-queue-core` capability describing the async `TaskQueue` API (`enqueue`, `get_result`, `close`).
- Define scheduling semantics using an optional `eta` parameter and internal `available_at` timestamps for immediate and delayed tasks.
- Define the public `Result` data model returned by `get_result`, including statuses, payload fields, and timestamps.

## Impact
- Affected specs: `task-queue-core`
- Affected code: `src/sitq/queue.py`, `src/sitq/result.py` (or equivalent core modules)

