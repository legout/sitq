## ADDED Requirements

### Requirement: TaskQueue configuration and defaults
The system SHALL allow configuring the async `TaskQueue` with optional backend, serializer, and a default result timeout, and SHALL support use as an async context manager.

#### Scenario: Construct TaskQueue with defaults
- **WHEN** a caller constructs `TaskQueue()` without passing a `backend` or `serializer`
- **THEN** the system SHALL create a default `SQLiteBackend` instance with a sensible default database path
- **AND** it SHALL use the default cloudpickle-based serializer for task payloads and results

#### Scenario: Default result timeout
- **WHEN** a caller constructs `TaskQueue(default_result_timeout=T)` with a non-`None` timeout `T`
- **AND** later calls `TaskQueue.get_result(task_id, timeout=None)`
- **THEN** the system SHALL wait for a result using `T` as the timeout
- **AND** a non-`None` `timeout` argument on `get_result` SHALL override the default

#### Scenario: Use TaskQueue as async context manager
- **WHEN** a caller uses `async with TaskQueue(...) as queue:` 
- **THEN** the TaskQueue SHALL ensure any required backend connections are established for use inside the block
- **AND** it SHALL close the backend and release resources when the context manager exits

### Requirement: Task context support
The system SHALL support an optional `context` dictionary on `TaskQueue.enqueue` that is persisted as part of the task payload for potential future use.

#### Scenario: Preserve task context in payload
- **WHEN** a caller invokes `TaskQueue.enqueue(func, *args, context={"request_id": "abc"}, **kwargs)`
- **THEN** the TaskQueue SHALL include the provided `context` in the serialized payload it passes to the backend
- **AND** the backend SHALL persist this context so that future worker implementations MAY access it when executing the task

