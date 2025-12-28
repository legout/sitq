## MODIFIED Requirements

### Requirement: Async TaskQueue API
The system SHALL provide an async-first `TaskQueue` API for enqueueing background tasks and retrieving their results.

#### Scenario: Get result not ready returns None
- **WHEN** a caller invokes `TaskQueue.get_result(task_id, timeout)` and the task is not complete before `timeout` expires
- **THEN** the system SHALL return `None`
- **AND** the system SHALL NOT raise a domain timeout exception to the caller for this case

