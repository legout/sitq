## MODIFIED Requirements

### Requirement: Bounded concurrency
The worker SHALL execute tasks with bounded concurrency using an internal limit.

#### Scenario: Acquire concurrency permit before dispatch
- **WHEN** the worker is about to dispatch a reserved task for execution
- **THEN** it SHALL first acquire capacity against its configured `max_concurrency` limit
- **AND** it SHALL NOT dispatch additional tasks while at the concurrency limit

#### Scenario: Stop waits for tracked in-flight tasks
- **WHEN** `worker.stop()` is called
- **THEN** the worker SHALL stop reserving new tasks
- **AND** it SHALL await all tasks it has already dispatched before returning

