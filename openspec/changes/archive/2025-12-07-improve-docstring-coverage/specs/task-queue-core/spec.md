## MODIFIED Requirements
### Requirement: Async TaskQueue API
The system SHALL provide an async-first `TaskQueue` API for enqueueing background tasks and retrieving their results with comprehensive documentation.

#### Scenario: Enqueue task with default settings
- **WHEN** a caller invokes `TaskQueue.enqueue(func, *args, **kwargs)` without an `eta`
- **THEN** the system SHALL create a new `task_id` and persist a pending task associated with that `task_id`
- **AND** the task SHALL be eligible for execution as soon as a worker polls the backend
- **AND** the method SHALL be documented with complete Args, Returns, and Raises sections

#### Scenario: Get result with timeout
- **WHEN** a caller invokes `TaskQueue.get_result(task_id, timeout)` and the task completes before `timeout` expires
- **THEN** the system SHALL return a `Result` instance for that `task_id`
- **AND** the `Result.status` SHALL be either `"success"` or `"failed"` depending on task execution
- **AND** the method SHALL be documented with parameter types and exception conditions

#### Scenario: Context manager usage
- **WHEN** a caller uses `TaskQueue` as an async context manager
- **THEN** the system SHALL automatically connect to the backend on entry
- **AND** SHALL automatically close the backend on exit
- **AND** both `__aenter__` and `__aexit__` methods SHALL have proper docstrings

## ADDED Requirements
### Requirement: Public API Definition
The system SHALL clearly define its public API through proper module exports and documentation.

#### Scenario: Import public API
- **WHEN** a developer imports from `sitq`
- **THEN** the system SHALL expose only public APIs through `__init__.py`
- **AND** SHALL provide clear `__all__` lists in each module
- **AND** SHALL hide internal implementation details

#### Scenario: API Documentation Generation
- **WHEN** documentation tools process the source code
- **THEN** the system SHALL provide complete docstrings for all public APIs
- **AND** SHALL follow consistent Google-style format
- **AND** SHALL include type hints, parameter descriptions, and usage examples