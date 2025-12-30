# Design: High-coverage examples suite

## Goals

- Each example is runnable on a fresh checkout with only sitq installed and SQLite available.
- Each example demonstrates one primary sitq capability and avoids overlapping heavily with others.
- Examples are robust and deterministic (bounded runtime, clean DB lifecycle, clear outputs).

## Conventions

### Layout

- `examples/basic/` contains the runnable scripts intended for first-time users.
- `examples/advanced/` (optional) is reserved for larger, real-world integrations; not required for this change.

### Runtime and cleanup

- Each script SHOULD complete within 30 seconds.
- Each script SHOULD create its own SQLite database using `tempfile.TemporaryDirectory()` and a file-backed DB path (not `:memory:`) so that worker/client separation patterns remain valid.
- Scripts SHOULD use `asyncio.run(main())` for async entry points and exit with status code `0` on success.

### API boundaries

- Scripts MUST use only public imports from `sitq` (e.g. `from sitq import TaskQueue, Worker, SQLiteBackend, SyncTaskQueue`).
- Scripts MUST NOT reference future/unimplemented features (retries, priorities, status APIs, batch enqueue helpers).

### Example-specific design notes

- `01_end_to_end.py`: includes `TaskQueue.get_result()` and `TaskQueue.deserialize_result()` to demonstrate the full “enqueue → execute → result” loop.
- `02_eta_delayed_execution.py`: uses a timezone-aware UTC `eta` and demonstrates that tasks are not executed before eligibility.
- `03_bounded_concurrency.py`: uses tasks with controlled sleep to make concurrency observable and verifies the bounded concurrency behavior via elapsed time or counters.
- `04_failures_and_tracebacks.py`: uses a task that raises and shows `Result.status == "failed"` plus `error` and `traceback`.
- `05_sync_client_with_worker.py`: demonstrates a sync producer using `SyncTaskQueue` interacting with a separate async worker against the same SQLite DB file.

