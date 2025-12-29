## ADDED Requirements

### Requirement: Test suite structure
The repository SHALL organize tests into a conventional directory structure to improve clarity and maintainability.

#### Scenario: Developer discovers tests
- **WHEN** a developer looks for automated checks
- **THEN** unit, integration, and performance tests SHALL be discoverable under a `tests/` directory
- **AND** performance/benchmark tests SHALL be clearly separated from unit/integration tests

### Requirement: Default test run excludes benchmarks
The default `pytest` invocation SHALL exclude long-running benchmarks/performance tests.

#### Scenario: Fast feedback loop
- **WHEN** a developer runs `pytest` with no special flags
- **THEN** only unit and integration tests SHALL execute by default
- **AND** performance tests SHALL require an explicit opt-in mechanism (e.g. a marker or dedicated command)

