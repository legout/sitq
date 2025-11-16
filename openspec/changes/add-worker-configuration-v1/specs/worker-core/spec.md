## ADDED Requirements

### Requirement: Worker configuration parameters
The Worker SHALL expose explicit configuration parameters for concurrency and polling behavior.

#### Scenario: Construct Worker with defaults
- **WHEN** a caller constructs `Worker(backend, serializer)` without overriding configuration
- **THEN** the Worker SHALL use a sensible default `max_concurrency` value
- **AND** it SHALL use a sensible default `poll_interval` in seconds for empty-queue backoff
- **AND** it SHALL use a sensible default `batch_size` for the maximum number of tasks reserved per poll

#### Scenario: Configure Worker concurrency and batch size
- **WHEN** a caller constructs `Worker(backend, serializer, max_concurrency=C, batch_size=B)` with positive integers `C` and `B`
- **THEN** the Worker SHALL limit the number of tasks executing concurrently to at most `C`
- **AND** on each poll it SHALL request at most `B` tasks from `backend.reserve`
- **AND** it SHALL further cap the number of newly reserved tasks so that the total number of running tasks never exceeds `max_concurrency`

