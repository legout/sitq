## MODIFIED Requirements
### Requirement: Worker start and polling loop
The system SHALL provide a `Worker` component that polls the backend for executable tasks and dispatches them for execution with comprehensive documentation.

#### Scenario: Start worker loop
- **WHEN** a `Worker` instance is started
- **THEN** it SHALL connect to the backend if necessary
- **AND** it SHALL periodically call `reserve` to fetch eligible tasks using a configurable poll interval
- **AND** the `start()` method SHALL be documented with complete parameter descriptions

#### Scenario: Stop worker gracefully
- **WHEN** `worker.stop()` is called while some tasks are still running
- **THEN** the worker SHALL stop reserving new tasks
- **AND** SHALL wait for all in-flight tasks to finish before returning
- **AND** the `stop()` method SHALL be documented with behavior guarantees

#### Scenario: Bounded concurrency
- **WHEN** the worker has already scheduled `max_concurrency` tasks for execution
- **THEN** it SHALL NOT dispatch additional tasks until at least one in-flight task completes
- **AND** the concurrency control SHALL be documented with examples

## ADDED Requirements
### Requirement: Worker API Documentation
The system SHALL provide complete documentation for all worker public methods and configuration options.

#### Scenario: Worker configuration
- **WHEN** a developer configures a Worker instance
- **THEN** all configuration parameters SHALL be documented with types, defaults, and usage examples
- **AND** SHALL include performance considerations for different settings
- **AND** SHALL document thread vs process execution trade-offs

#### Scenario: Task execution lifecycle
- **WHEN** a worker processes tasks
- **THEN** the complete lifecycle SHALL be documented from reservation to result storage
- **AND** SHALL include error handling and retry behavior
- **AND** SHALL provide examples of custom task execution patterns