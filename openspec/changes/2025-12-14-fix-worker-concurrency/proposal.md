# Change: Fix Worker Concurrency (Bounded Dispatch + Task Tracking)

## Why

The current `Worker` implementation does not reliably enforce `max_concurrency` because:

1. **Semaphore acquired after task creation**: The worker creates execution tasks via `_track_task()` and `_execute_task()` BEFORE acquiring the semaphore permit. This means all tasks are dispatched immediately, with the semaphore only delaying their execution (not their scheduling).

2. **Double task wrapping**: The code creates a "Task of Task" pattern where `_track_task()` wraps `_execute_task()` in one Task, then `asyncio.create_task()` wraps `_execute_with_semaphore()` in another Task. This adds overhead and makes shutdown tracking unreliable.

3. **Unreachable code in failure path**: A `logger.error()` call appears after unconditional `raise` statements in `_execute_task()`, making it unreachable.

4. **Inconsistent task tracking**: Only the inner tasks are tracked, not the outer semaphore-wrapper tasks, making shutdown behavior unpredictable.

This change restores the intended bounded concurrency semantics required by `worker-core`.

## What Changes

- **New dispatch architecture**: Create `_dispatch_task()` method that:
  - Acquires semaphore permit FIRST (before any task creation)
  - Checks for shutdown inside the semaphore block
  - Executes the task
  - Automatically releases semaphore via `async with`
  - Tracks the task for shutdown waiting

- **Remove double wrapping**: Eliminate `_execute_with_semaphore()` method and the double task creation pattern. Now there's exactly ONE task per reserved job.

- **Fix unreachable code**: Move `logger.error()` call BEFORE the `raise TaskExecutionError()` statements in `_execute_task()`.

- **Simplify polling loop**: Replace complex dispatch logic with simple call to `_dispatch_task()` for each reserved task.

## Impact

- Affected specs:
  - `worker-core`
- Affected code:
  - `src/sitq/worker.py` (~30 lines changed, `_execute_with_semaphore()` removed)
  - `test_worker_concurrency.py` (new test file with 3 test cases)
- **BREAKING**: None intended; this is a correctness/performance fix to match v1 worker semantics.

## Implementation Details

### New `_dispatch_task()` method
```python
async def _dispatch_task(self, reserved_task: ReservedTask) -> None:
    """Dispatch a reserved task with semaphore protection and tracking."""
    async def _run_with_semaphore():
        async with self._semaphore:  # Acquire FIRST
            if self._shutdown_event.is_set():
                logger.debug("Shutdown detected, skipping task execution")
                return
            await self._execute_task(reserved_task)

    self._track_task(_run_with_semaphore())  # Single tracked task
```

### Removed `_execute_with_semaphore()` method
No longer needed - semaphore handling moved into `_dispatch_task()`.

### Modified `_polling_loop()`
```python
# Before (lines 179-184):
for reserved_task in reserved_tasks:
    task_coro = self._execute_task(reserved_task)
    wrapped_task = self._track_task(task_coro)
    asyncio.create_task(self._execute_with_semaphore(wrapped_task))

# After (lines 179-180):
for reserved_task in reserved_tasks:
    self._dispatch_task(reserved_task)
```

## Tests Added

1. **`test_worker_never_exceeds_max_concurrency()`**: Uses barrier and counter to prove worker never exceeds max_concurrency
2. **`test_stop_waits_for_in_flight_tasks()`**: Verifies stop() waits for all tasks before returning
3. **`test_concurrency_with_failures()`**: Ensures task failures don't affect concurrency bounds or crash the worker

## Notes / Risks

- **Concurrency changes**: Can surface latent race conditions in tests. The new deterministic tests use barriers to ensure precise concurrency measurement.
- **Semaphore ordering**: Acquiring semaphore before task creation ensures we never create more than max_concurrency tasks, even if `reserve()` returns more items than available capacity.
- **Shutdown behavior**: Now properly waits for all tracked tasks because we track the actual execution tasks (not wrapper tasks).
- **Migration**: No database migration needed - this is purely runtime behavior change.

## Verification Steps

1. Run new concurrency tests: `pytest test_worker_concurrency.py -v`
2. Run all existing worker tests: `pytest test_worker*.py -v`
3. Verify no "Task of Task" patterns remain in code
4. Confirm unreachable code is eliminated (use static analysis if available)
