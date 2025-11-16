## MODIFIED Requirements

### Requirement: Basic worker logging
The worker SHALL emit basic logging events for lifecycle and task outcomes using the loguru library.

#### Scenario: Log task lifecycle events
- **WHEN** a task is reserved, started, completed, or failed
- **THEN** the worker SHALL emit log messages at info or debug level reflecting these events using loguru's logger

#### Scenario: Log worker lifecycle events
- **WHEN** the worker is started, stopped, or encounters errors
- **THEN** the worker SHALL emit appropriate log messages using loguru's logger

## ADDED Requirements

### Requirement: Loguru dependency
The project SHALL include loguru as a runtime dependency for enhanced logging capabilities.

#### Scenario: Install project dependencies
- **WHEN** sitq is installed or its dependencies are resolved
- **THEN** loguru SHALL be included as a required dependency

### Requirement: Structured logging with loguru
The worker SHALL leverage loguru's structured logging capabilities for better log formatting and exception handling.

#### Scenario: Enhanced exception logging
- **WHEN** a task fails with an exception
- **THEN** the worker SHALL use loguru's automatic exception capture to include detailed traceback information

#### Scenario: Configurable log formatting
- **WHEN** log messages are emitted
- **THEN** they SHALL use loguru's default formatting which includes timestamps, log levels, and structured output

### Requirement: Backward compatibility for logging configuration
The worker SHALL maintain backward compatibility for users who provide custom logger instances.

#### Scenario: Custom logger injection
- **WHEN** a logger instance is provided to the Worker constructor
- **THEN** the worker SHALL use the provided logger instead of loguru's default logger
- **AND** the interface SHALL remain compatible with existing code