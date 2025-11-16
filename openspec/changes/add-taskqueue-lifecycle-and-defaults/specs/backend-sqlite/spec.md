## ADDED Requirements

### Requirement: Backend lifecycle
The backend SHALL expose an explicit async lifecycle with `connect` and `close` operations to manage any underlying database connections.

#### Scenario: Connect backend before use
- **WHEN** a caller invokes `backend.connect()` on a `SQLiteBackend` instance before enqueueing or reserving tasks
- **THEN** the backend SHALL establish any required SQLite connections and configure them (including WAL mode) for subsequent operations
- **AND** repeated calls to `connect()` SHALL be safe and SHALL NOT create duplicate connections visible to callers

#### Scenario: Close backend after use
- **WHEN** a caller invokes `backend.close()` after it has finished using the backend
- **THEN** the backend SHALL close any open SQLite connections and release associated resources

### Requirement: Backend task timestamps
The SQLite backend SHALL track canonical timing information for tasks in a way that supports the v1 Result model.

#### Scenario: Set enqueued_at on enqueue
- **WHEN** the core calls `backend.enqueue(task_id, payload, available_at)`
- **THEN** the SQLite backend SHALL populate an `enqueued_at` timestamp for the new task row using a timezone-aware UTC value

#### Scenario: Set started_at on reserve
- **WHEN** the core calls `backend.reserve(max_items, now)` and a task is transitioned from `pending` to `in_progress`
- **THEN** the SQLite backend SHALL set the task's `started_at` timestamp to a timezone-aware UTC value that reflects when the worker reserved the task

