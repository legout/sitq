# sync-task-queue Specification

## Purpose
TBD - created by archiving change add-sync-task-queue. Update Purpose after archive.
## Requirements
### Requirement: SyncTaskQueue wrapper API
The system SHALL provide a `SyncTaskQueue` wrapper that exposes a blocking interface over the async `TaskQueue`.

#### Scenario: SyncTaskQueue methods are available as instance methods
- **WHEN** a caller constructs `SyncTaskQueue(...)`
- **THEN** the instance SHALL expose `__enter__`, `__exit__`, `enqueue`, and `get_result` as callable instance methods
- **AND** these methods SHALL delegate to the underlying async `TaskQueue` using an event loop owned by `SyncTaskQueue`

### Requirement: Event loop ownership and constraints
The sync wrapper SHALL own its event loop and SHALL NOT require an existing loop.

#### Scenario: Use in non-async environment
- **WHEN** `SyncTaskQueue` is used in a main thread without an existing event loop
- **THEN** it SHALL create and manage an event loop as needed for the underlying async operations

#### Scenario: Guidance for async environments
- **WHEN** a user is writing code inside an existing async framework (for example FastAPI or Starlette handlers)
- **THEN** documentation SHALL recommend using the async `TaskQueue` directly instead of `SyncTaskQueue`

