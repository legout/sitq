## MODIFIED Requirements

### Requirement: SyncTaskQueue wrapper API
The system SHALL provide a `SyncTaskQueue` wrapper that exposes a blocking interface over the async `TaskQueue`.

#### Scenario: SyncTaskQueue methods are available as instance methods
- **WHEN** a caller constructs `SyncTaskQueue(...)`
- **THEN** the instance SHALL expose `__enter__`, `__exit__`, `enqueue`, and `get_result` as callable instance methods
- **AND** these methods SHALL delegate to the underlying async `TaskQueue` using an event loop owned by `SyncTaskQueue`

