## 1. Implementation

- [x] Remove tracked `__pycache__` / `.pyc` artifacts and update `.gitignore` so bytecode is never committed.
- [x] Fix `TaskQueue` initialization so `__init__` exists and assigns `backend` and `serializer` consistently.
- [x] Ensure `TaskQueue.get_result(task_id, timeout)` returns `None` on timeout without raising/wrapping a timeout exception.
- [x] Fix `SyncTaskQueue` so `__enter__` and `get_result` are proper class methods (not module-level functions).
- [x] Ensure `SyncTaskQueue` uses sitq domain exceptions for operational failures (no bare `RuntimeError` for enqueue/get_result failures).
- [ ] Ensure serializer can serialize/deserialize `None` results.
- [ ] Fix SQLite backend transaction/connection scope issues that can leak or operate on closed connections (e.g. commits outside of `async with` connection scope).
- [ ] Fix validation API inconsistencies that cause runtime failures (e.g. missing builder methods used in v1 codepaths, and missing `.validate()` calls that silently skip validation).
- [x] Add missing `error` column to SQLite `results` table schema.
- [x] Add automatic migration for SQLite schema changes.
- [x] Remove debug `print()` statements and replace with loguru logging.
- [x] Fix `SyncTaskQueue` event loop detection to properly reject async contexts.
- [x] Fix timeout semantics (`timeout=0` issue).

## 2. Tests

- [x] Add/adjust tests for `TaskQueue.get_result` timeout semantics (`None` on timeout).
- [x] Add/adjust tests that import and exercise `SyncTaskQueue` end-to-end against `SQLiteBackend`.
- [x] Add/adjust tests for serializing/deserializing a `None` task return value.
- [x] Run full test suite and confirm clean import from source (no reliance on committed bytecode).

## 3. Validation

- [x] Verify `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -c "import sitq"` succeeds.
- [x] Run a minimal end-to-end example (enqueue → worker processes → get_result) for both async and sync APIs.