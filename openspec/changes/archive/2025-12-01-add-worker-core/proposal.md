# Change: Add async Worker for executing tasks from the backend

## Why
sitq v1 needs a single worker abstraction that polls the backend, executes tasks with bounded concurrency, and records results.

## What Changes
- Introduce a `worker-core` capability describing the `Worker` API (`start`, `stop`) and its polling, reservation, and execution behavior.
- Define concurrency control, graceful shutdown semantics, and basic logging for task lifecycle events.
- Describe how the worker uses the serializer and backend to execute both async and sync callables.

## Impact
- Affected specs: `worker-core`
- Affected code: `src/sitq/worker.py`

