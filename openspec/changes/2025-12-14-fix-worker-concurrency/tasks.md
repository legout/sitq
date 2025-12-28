## 1. Implementation

- [x] Ensure the worker computes available capacity (`max_concurrency - running`) and reserves at most that many tasks.
- [x] Acquire an `asyncio.Semaphore` permit before creating the execution task.
- [x] Track the created execution tasks in an internal set until completion.
- [x] Ensure task failures do not crash the polling loop and are recorded via `mark_failure`.
- [x] Ensure `stop()` stops reserving new work and awaits all tracked in-flight tasks.
- [x] Remove redundant asyncio task wrapping (avoid "Task of Task" patterns).
- [x] Remove unreachable code in failure paths (no code after an unconditional `raise`).

## 2. Tests

- [x] Add/adjust tests proving the worker never runs more than `max_concurrency` tasks at once.
- [x] Add/adjust tests proving `stop()` waits for in-flight work to complete.
- [x] Add/adjust tests proving failures are recorded and do not terminate the worker loop.

## 3. Validation

- [x] Run an integration test that enqueues many tasks and confirms bounded concurrency via timestamps/counters.
