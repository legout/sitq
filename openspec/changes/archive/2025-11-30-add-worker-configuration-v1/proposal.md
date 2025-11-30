# Change: Add explicit Worker configuration parameters for v1

## Why
The `worker-core` spec describes the Worker’s behavior (polling, bounded concurrency, graceful shutdown), but it does not yet capture the explicit API surface and configuration knobs defined in `SPEC_v1.md` (e.g. `max_concurrency`, `poll_interval`, `batch_size`). Making these parameters part of the specification will clarify how callers control Worker behavior and how the worker chooses how many tasks to reserve on each poll.

## What Changes
- Extend the `worker-core` capability to document the Worker constructor parameters, including `max_concurrency`, `poll_interval`, and `batch_size`.
- Specify how the Worker uses `max_concurrency` together with the current number of in-flight tasks to decide how many new tasks to reserve.
- Specify how `batch_size` limits the number of tasks reserved per poll independently of the concurrency limit.

## Impact
- Affected specs: `worker-core`
- Affected code: `src/sitq/worker.py`, `tests/test_worker_core.py`

