# worker-core Specification

## Purpose
TBD - created by archiving change add-worker-core. Update Purpose after archive.
## Requirements
### Requirement: Worker start and polling loop
The system SHALL provide a `Worker` component that polls the backend for executable tasks and dispatches them for execution.

#### Scenario: Start worker loop
- **WHEN** a `Worker` instance is started
- **THEN** it SHALL connect to the backend if necessary
- **AND** it SHALL periodically call `reserve` to fetch eligible tasks using a configurable poll interval

#### Scenario: No tasks available
- **WHEN** the worker polls the backend and `reserve` returns no tasks
- **THEN** the worker SHALL wait for at least the configured poll interval before polling again

### Requirement: Bounded concurrency
The worker SHALL execute tasks with bounded concurrency using an internal limit.

#### Scenario: Limit concurrent tasks
- **WHEN** the worker has already scheduled `max_concurrency` tasks for execution
- **THEN** it SHALL NOT dispatch additional tasks until at least one in-flight task completes

### Requirement: Task execution and result recording
The worker SHALL execute reserved tasks using the configured serializer and backend and record success or failure.

#### Scenario: Execute async callable
- **WHEN** a reserved task payload deserializes to an async callable and arguments
- **THEN** the worker SHALL await the callable
- **AND** on success SHALL call `mark_success` with the serialized return value

#### Scenario: Execute sync callable
- **WHEN** a reserved task payload deserializes to a synchronous callable and arguments
- **THEN** the worker SHALL execute the callable using an executor compatible with `asyncio`
- **AND** on success SHALL call `mark_success` with the serialized return value

#### Scenario: Handle task failure
- **WHEN** a callable raises an exception during execution
- **THEN** the worker SHALL capture the error and traceback
- **AND** SHALL call `mark_failure` for the task

### Requirement: At-least-once delivery semantics
The worker and backend combination SHALL provide at-least-once delivery of tasks and SHALL NOT guarantee exactly-once execution.

#### Scenario: Task retried after worker crash
- **WHEN** a worker crashes or is terminated after reserving a task but before calling `mark_success` or `mark_failure`
- **THEN** the system MAY later make that task eligible for execution again so that another worker can retry it

### Requirement: Graceful shutdown
The worker SHALL support graceful shutdown that stops polling and waits for running tasks to complete.

#### Scenario: Stop worker with in-flight tasks
- **WHEN** `worker.stop()` is called while some tasks are still running
- **THEN** the worker SHALL stop reserving new tasks
- **AND** SHALL wait for all in-flight tasks to finish before returning

### Requirement: Basic worker logging
The worker SHALL emit basic logging events for lifecycle and task outcomes using the loguru library.

#### Scenario: Log task lifecycle events
- **WHEN** a task is reserved, started, completed, or failed
- **THEN** the worker SHALL emit log messages at info or debug level reflecting these events

