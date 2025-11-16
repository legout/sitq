## ADDED Requirements

### Requirement: Async TaskQueue API
The system SHALL provide an async-first `TaskQueue` API for enqueueing background tasks and retrieving their results.

#### Scenario: Enqueue task with default settings
- **WHEN** a caller invokes `TaskQueue.enqueue(func, *args, **kwargs)` without an `eta`
- **THEN** the system SHALL create a new `task_id` and persist a pending task associated with that `task_id`
- **AND** the task SHALL be eligible for execution as soon as a worker polls the backend

#### Scenario: Get result with timeout
- **WHEN** a caller invokes `TaskQueue.get_result(task_id, timeout)` and the task completes before `timeout` expires
- **THEN** the system SHALL return a `Result` instance for that `task_id`
- **AND** the `Result.status` SHALL be either `"success"` or `"failed"` depending on task execution

#### Scenario: Get result not ready
- **WHEN** a caller invokes `TaskQueue.get_result(task_id, timeout)` and the task is not complete before `timeout` expires
- **THEN** the system SHALL return `None`

### Requirement: Result model
The system SHALL expose a `Result` data object describing the outcome of a task execution.

#### Scenario: Successful result
- **WHEN** a task finishes successfully
- **THEN** the system SHALL persist and return a `Result` where `status` is `"success"`
- **AND** `value` SHALL contain the serialized return value
- **AND** `error` and `traceback` SHALL be `None`
- **AND** `enqueued_at` and `finished_at` SHALL be populated with UTC timestamps

#### Scenario: Failed result
- **WHEN** a task raises an exception during execution
- **THEN** the system SHALL persist and return a `Result` where `status` is `"failed"`
- **AND** `error` SHALL contain a human-readable error message
- **AND** `traceback` SHALL contain a formatted stack trace
- **AND** `finished_at` SHALL be populated with a UTC timestamp

### Requirement: ETA scheduling semantics
The system SHALL support immediate and delayed execution of tasks using an optional `eta` parameter.

#### Scenario: Immediate task scheduling
- **WHEN** a caller enqueues a task with `eta=None`
- **THEN** the system SHALL set the task's `available_at` timestamp to the current UTC time
- **AND** workers SHALL treat the task as eligible for execution as soon as they poll

#### Scenario: Delayed task scheduling
- **WHEN** a caller enqueues a task with a timezone-aware UTC `eta` in the future
- **THEN** the system SHALL set the task's `available_at` timestamp to `eta`
- **AND** workers SHALL NOT execute the task before `available_at <= now` in UTC

