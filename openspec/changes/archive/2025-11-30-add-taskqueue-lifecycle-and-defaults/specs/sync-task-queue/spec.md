## ADDED Requirements

### Requirement: SyncTaskQueue default result timeout
The synchronous wrapper SHALL mirror the default result timeout behavior of the async `TaskQueue`.

#### Scenario: Use SyncTaskQueue with default_result_timeout
- **WHEN** a caller constructs `SyncTaskQueue(..., default_result_timeout=T)` with a non-`None` timeout `T`
- **AND** later calls `queue.get_result(task_id)` without passing a `timeout`
- **THEN** the wrapper SHALL delegate to the underlying async `TaskQueue.get_result` using `T` as the timeout
- **AND** a non-`None` `timeout` argument on `SyncTaskQueue.get_result` SHALL override the default for that call

