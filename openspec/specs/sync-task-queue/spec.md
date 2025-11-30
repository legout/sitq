# sync-task-queue Specification

## Purpose
TBD - created by archiving change add-sync-task-queue. Update Purpose after archive.
## Requirements
### Requirement: SyncTaskQueue wrapper API
The system SHALL provide a `SyncTaskQueue` wrapper that exposes a blocking interface over the async `TaskQueue`.

#### Scenario: Use SyncTaskQueue as context manager
- **WHEN** a caller uses `with SyncTaskQueue(...) as queue:` in synchronous code
- **THEN** the wrapper SHALL create and manage any required async resources
- **AND** the caller SHALL be able to call `queue.enqueue` and `queue.get_result` using blocking semantics

#### Scenario: Delegate to async TaskQueue
- **WHEN** `SyncTaskQueue.enqueue` or `SyncTaskQueue.get_result` is called
- **THEN** the wrapper SHALL internally delegate to the corresponding async `TaskQueue` methods using an event loop it controls

### Requirement: Event loop ownership and constraints
The sync wrapper SHALL own its event loop and SHALL NOT require an existing loop.

#### Scenario: Use in non-async environment
- **WHEN** `SyncTaskQueue` is used in a main thread without an existing event loop
- **THEN** it SHALL create and manage an event loop as needed for the underlying async operations

#### Scenario: Guidance for async environments
- **WHEN** a user is writing code inside an existing async framework (for example FastAPI or Starlette handlers)
- **THEN** documentation SHALL recommend using the async `TaskQueue` directly instead of `SyncTaskQueue`

### Requirement: SyncTaskQueue default result timeout
The synchronous wrapper SHALL mirror the default result timeout behavior of the async `TaskQueue`.

#### Scenario: Use SyncTaskQueue with default_result_timeout
- **WHEN** a caller constructs `SyncTaskQueue(..., default_result_timeout=T)` with a non-`None` timeout `T`
- **AND** later calls `queue.get_result(task_id)` without passing a `timeout`
- **THEN** the wrapper SHALL delegate to the underlying async `TaskQueue.get_result` using `T` as the timeout
- **AND** a non-`None` `timeout` argument on `SyncTaskQueue.get_result` SHALL override the default for that call

