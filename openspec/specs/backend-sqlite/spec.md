# backend-sqlite Specification

## Purpose
TBD - created by archiving change add-backend-sqlite. Update Purpose after archive.
## Requirements
### Requirement: Backend protocol
The system SHALL define an async backend protocol responsible for persisting tasks and results independently of the public queue API.

#### Scenario: Enqueue task in backend
- **WHEN** the core calls `backend.enqueue(task_id, payload, available_at)`
- **THEN** the backend SHALL persist a new row representing the task with a `pending` status and the given `available_at` timestamp

#### Scenario: Reserve tasks for execution
- **WHEN** the core calls `backend.reserve(max_items, now)` with a positive `max_items`
- **THEN** the backend SHALL atomically select up to `max_items` tasks with status `pending` and `available_at <= now`
- **AND** the backend SHALL transition those tasks to an `in_progress` state and set their `started_at` timestamps
- **AND** the backend SHALL return `ReservedTask` instances describing the reserved tasks

### Requirement: SQLiteBackend storage
The system SHALL provide a `SQLiteBackend` implementation that uses a local SQLite database file to store tasks and results.

#### Scenario: Create tables on first use
- **WHEN** `SQLiteBackend` connects to a database file that does not yet contain the tasks table
- **THEN** it SHALL create the tasks table with columns for identifiers, status, payload, timing fields, result value, error, and traceback

#### Scenario: Persist task results
- **WHEN** the core calls `mark_success` or `mark_failure` for a given `task_id`
- **THEN** `SQLiteBackend` SHALL update the corresponding row with the final status, result data or error details, and `finished_at` timestamp

### Requirement: Result lookup by task_id
The backend SHALL return `Result` objects for completed tasks when queried by `task_id`.

#### Scenario: Get existing result
- **WHEN** the core calls `backend.get_result(task_id)` for a task that has completed
- **THEN** the backend SHALL return a `Result` object matching the persisted row

#### Scenario: Get missing result
- **WHEN** the core calls `backend.get_result(task_id)` for a task that does not exist
- **THEN** the backend SHALL return `None`

### Requirement: SQLite concurrency configuration
The SQLite backend SHALL enable write-ahead logging (WAL) mode where supported to allow multiple workers to read and write concurrently to the same database file.

#### Scenario: Enable WAL mode on connect
- **WHEN** `SQLiteBackend` connects to the database file on a platform that supports WAL mode
- **THEN** it SHALL configure the connection to use WAL mode for improved concurrency

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

