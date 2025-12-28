# Implementation Order for OpenSpec Changes (v1 Refactor)

This document defines the recommended implementation order for the **active** OpenSpec changes under `openspec/changes/` and highlights what can be done in parallel.

## Active Changes

1. `2025-12-14-stabilize-v1-core`
2. `2025-12-14-fix-worker-concurrency`
3. `2025-12-14-test-suite-organization`
4. `2025-12-14-align-docs-and-deps-v1`

## Recommended Order

### 1) `2025-12-14-stabilize-v1-core` (foundation)
**Why first**
- Unblocks everything else by restoring importability and clarifying core semantics (notably `TaskQueue.get_result(..., timeout)` returns `None`).
- Fixes baseline issues in `TaskQueue`, `SyncTaskQueue`, serializer, validation, and SQLite connection/transaction handling that can otherwise derail any follow-on work.

**Primary outputs**
- Clean imports from source (no reliance on committed bytecode artifacts).
- Stable, spec-aligned behavior for timeout and sync wrapper error handling.

### 2) `2025-12-14-fix-worker-concurrency` (correctness + performance)
**Why second**
- Depends on a stable core import surface and baseline backend behavior.
- Establishes correct bounded concurrency and reliable shutdown semantics, which improves both real usage and test determinism.

**Primary outputs**
- Semaphore/dispatch logic that enforces `max_concurrency`.
- Reliable task tracking so `stop()` waits for in-flight work.

### 3) `2025-12-14-test-suite-organization` (reduce friction)
**Why third**
- Moving/renaming tests tends to create merge conflicts; doing it after the main functional fixes reduces churn.
- Once core behavior stabilizes, you can reorganize tests without repeatedly revisiting paths/import conventions.

**Primary outputs**
- `tests/` layout (unit/integration vs performance).
- Benchmarks opt-in (default `pytest` stays fast).

### 4) `2025-12-14-align-docs-and-deps-v1` (user-facing alignment)
**Why last**
- Docs and examples should reflect the final stabilized API semantics and worker behavior.
- Dependency trimming is safer once you’ve confirmed what v1 runtime code actually imports/needs.

**Primary outputs**
- README/MkDocs aligned to v1 scope.
- Runnable `examples/` “first success” script.
- Reduced default dependencies; deferred backends moved to optional installs (if desired).

## Parallelization Guidance

You *can* implement some of these in parallel, but expect merge conflicts if two efforts touch the same files.

### Safe(ish) parallel tracks (recommended)
- After (1) is merged:
  - Track A: implement (2) `fix-worker-concurrency`
  - Track B: implement (4) `align-docs-and-deps-v1` **only for docs** (README/docs edits)

Rationale: worker concurrency changes mostly touch `src/sitq/worker.py`, while docs work mostly touches `README.md` and `docs/**`.

### Parallel tracks with higher conflict risk
- (3) `test-suite-organization` in parallel with (1) or (2):
  - likely conflicts because both phases typically modify tests, imports, and CI/pytest configuration.

If you want to parallelize this anyway, do it on a separate branch and merge it only once (1) and (2) are stable, then resolve conflicts once.

## Validation Checkpoints (recommended)

After each change-id is implemented:
- Run `openspec validate <change-id> --strict`
- Run the default pytest suite (fast path; exclude performance tests by default)
- Run one end-to-end example (enqueue → worker → get_result) to confirm the user workflow
