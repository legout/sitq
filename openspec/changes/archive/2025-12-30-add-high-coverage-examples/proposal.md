# Change: Add high-coverage runnable examples

## Why

The repository currently has a small set of example scripts, but they do not provide a clear, end-to-end “first success” path that exercises the implemented v1 workflow (enqueue → worker executes → result retrieval and deserialization). Some examples also avoid or disclaim core behavior, which reduces user confidence and makes it harder to learn sitq by running code.

We want a minimal set of **clearly distinct**, **immediately runnable** examples that cover the main v1 features without referencing unimplemented APIs (retries, priorities, task status/metrics, multiple backends).

## What Changes

- Add a curated set of runnable scripts under `examples/basic/`:
  - `01_end_to_end.py`: enqueue (async + sync), run worker, get and deserialize results.
  - `02_eta_delayed_execution.py`: delayed execution using `eta` (timezone-aware UTC).
  - `03_bounded_concurrency.py`: bounded concurrency with `Worker(max_concurrency=...)`.
  - `04_failures_and_tracebacks.py`: task failure recorded in `Result` (error + traceback).
  - `05_sync_client_with_worker.py`: sync producer (`SyncTaskQueue`) interacting with an async worker via a shared SQLite DB.
- Add `examples/README.md` to describe the learning path and how each example maps to sitq features.
- Update documentation “Getting Started” entry points (e.g. `docs/quickstart.md`) to link to at least one runnable example and recommend an order.
- Add a validation check to ensure examples remain runnable (e.g. `tests/validation/test_examples.py` running the scripts with timeouts).

## Impact

- Affected specs:
  - `documentation-examples` (example set definition and quality constraints)
  - `documentation-system` (ensure getting-started links to runnable examples)
  - `testing-system` (validate examples are runnable as part of validation tests)
- Affected code/content:
  - `examples/` (new scripts + README)
  - `docs/` (linking and example references)
  - `tests/validation/` (example execution validation)

## Non-goals

- Introducing new sitq runtime features (retries, priorities, task status APIs, multiple backends).
- Adding external infrastructure dependencies (Redis/Postgres/NATS) for examples.

