# Change: Add SyncTaskQueue convenience wrapper

## Why
sitq v1 targets both async and sync Python code. A thin synchronous wrapper is needed so scripts without an event loop can enqueue tasks and wait for results using the same semantics as the async `TaskQueue`.

## What Changes
- Introduce a `sync-task-queue` capability that describes the `SyncTaskQueue` API and its relationship to the async `TaskQueue`.
- Define how the sync wrapper owns and manages an event loop under the hood.
- Clarify the intended usage constraints (sync-only contexts, not inside existing event loops).

## Impact
- Affected specs: `sync-task-queue`
- Affected code: `src/sitq/sync.py`

