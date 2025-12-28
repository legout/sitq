## 1. Implementation

- [ ] Ensure the worker computes available capacity (`max_concurrency - running`) and reserves at most that many tasks.
- [ ] Acquire an `asyncio.Semaphore` permit before creating the execution task.
- [ ] Track the created execution tasks in an internal set until completion.
- [ ] Ensure task failures do not crash the polling loop and are recorded via `mark_failure`.
- [ ] Ensure `stop()` stops reserving new work and awaits all tracked in-flight tasks.
- [ ] Remove redundant asyncio task wrapping (avoid “Task of Task” patterns).
- [ ] Remove unreachable code in failure paths (no code after an unconditional `raise`).

## 2. Tests

- [ ] Add/adjust tests proving the worker never runs more than `max_concurrency` tasks at once.
- [ ] Add/adjust tests proving `stop()` waits for in-flight work to complete.
- [ ] Add/adjust tests proving failures are recorded and do not terminate the worker loop.

## 3. Validation

- [ ] Run an integration test that enqueues many tasks and confirms bounded concurrency via timestamps/counters.
