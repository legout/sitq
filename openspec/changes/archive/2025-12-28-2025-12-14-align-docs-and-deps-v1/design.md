# Design: Align Docs and Dependencies to v1

## Goals

- Provide a single, reliable “first success” runnable script under `examples/`.
- Make documentation snippets reflect the **actual** async-first public API exported by `sitq`.
- Reduce confusion by removing or explicitly labeling unimplemented features in docs.
- Reduce default install footprint by keeping only v1 runtime dependencies in `[project].dependencies`.

## Non-Goals

- Implementing deferred backends (Redis/Postgres/NATS) or multiple worker types.
- Introducing new runtime dependencies or external services for examples.

## Approach

### Runnable Script as the Source of Truth

- Add a canonical runnable example (e.g. `examples/basic/quickstart_async.py`) demonstrating:
  - `SQLiteBackend("...")` setup
  - `TaskQueue.enqueue(func, ...)`
  - running a `Worker` long enough to process tasks
  - retrieving + printing a deserialized result
- Documentation should reference this script and reuse its code rather than maintaining divergent snippets.

### Documentation Alignment

- Update quickstart and core guides to use the same API surface as the runnable script.
- Where docs reference non-existent APIs:
  - remove the section, or
  - rewrite it to match what is implemented, or
  - clearly mark it as “future/roadmap”.

### Validation

- Keep validation lightweight:
  - `python -m py_compile` for syntax/importability
  - run existing documentation validation scripts
  - run the runnable example script as a drift check

