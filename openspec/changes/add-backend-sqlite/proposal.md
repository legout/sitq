# Change: Add backend interface and SQLiteBackend implementation

## Why
sitq v1 requires a single, reliable, file-backed backend so workers and queues can persist tasks and results without external infrastructure.

## What Changes
- Introduce a backend protocol describing the async operations required by the core (`enqueue`, `reserve`, `mark_success`, `mark_failure`, `get_result`, and lifecycle methods).
- Specify a `SQLiteBackend` implementation that stores tasks and results in a local SQLite database file and supports basic multi-process workers.
- Define the task table schema and atomic reservation behavior used by workers.

## Impact
- Affected specs: `backend-sqlite`
- Affected code: `src/sitq/backends/base.py`, `src/sitq/backends/sqlite.py`

