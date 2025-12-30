# testing-system Specification

## ADDED Requirements

### Requirement: Validate runnable examples
The repository SHALL validate that runnable example scripts execute successfully in the automated test suite.

#### Scenario: Validation test executes examples
- **WHEN** a developer runs `pytest`
- **THEN** the validation tests SHALL execute each script under `examples/basic/` with a timeout
- **AND** the test SHALL fail if any example exits non-zero or times out

