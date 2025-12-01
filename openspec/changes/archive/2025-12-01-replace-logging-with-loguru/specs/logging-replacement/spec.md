# Specification: Replace Logging with Loguru

## ADDED Requirements

### Requirement: Replace logging module with loguru
The sitq codebase SHALL replace the standard Python `logging` module with `loguru` for improved logging capabilities and developer experience.

#### Scenario: Worker lifecycle logging
**GIVEN** a worker is started, stopped, or encounters lifecycle events
**WHEN** logging events occur
**THEN** the worker SHALL use loguru for emitting log messages at appropriate levels
**AND** log messages SHALL maintain the same content and levels as the current implementation

#### Scenario: Task execution logging
**GIVEN** a worker executes tasks (success, failure, start)
**WHEN** task execution events occur
**THEN** the worker SHALL use loguru to log task lifecycle events
**AND** exception handling and tracebacks SHALL be formatted using loguru's enhanced formatting

#### Scenario: Dependency management
**GIVEN** the project dependencies in pyproject.toml
**WHEN** loguru is added as a dependency
**THEN** loguru SHALL be included in the main dependencies list
**AND** the version SHALL be compatible with Python 3.13+

### Requirement: Maintain logging compatibility
The transition to loguru SHALL maintain backward compatibility for logging behavior and message content.

#### Scenario: Log level preservation
**GIVEN** existing logging calls at different levels (debug, info, warning, error)
**WHEN** migrated to loguru
**THEN** all log levels SHALL be preserved with equivalent loguru levels
**AND** log message content SHALL remain unchanged

#### Scenario: Exception logging
**GIVEN** task execution failures and exceptions
**WHEN** logged using loguru
**THEN** exception information and tracebacks SHALL be captured with enhanced formatting
**AND** the level of detail SHALL be equivalent or better than the current implementation

## MODIFIED Requirements

### Requirement: Basic worker logging (from add-worker-core)
The worker SHALL emit basic logging events for lifecycle and task outcomes using loguru instead of the standard logging library.

#### Scenario: Log task lifecycle events
**GIVEN** a task is reserved, started, completed, or failed
**WHEN** these lifecycle events occur
**THEN** the worker SHALL emit log messages at info or debug level using loguru
**AND** log messages SHALL reflect these events with loguru's enhanced formatting