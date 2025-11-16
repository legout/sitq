# Tasks: Replace Logging with Loguru

## Implementation Tasks

### 1. Add loguru dependency
- [x] Add `loguru>=0.7.0` to dependencies in pyproject.toml
- [x] Update lock file with `uv lock`

### 2. Update Worker class logging
- [x] Replace `import logging` with `from loguru import logger` in src/sitq/worker.py
- [x] Remove `logging.getLogger("sitq.worker")` initialization
- [x] Update all `self.logger.*` calls to use `logger.*` directly
- [x] Maintain backward compatibility in constructor (accept logger parameter but default to loguru)
- [x] Update type hints for logger parameter

### 3. Update test files
- [x] Replace logging configuration in tests/test_worker_core.py
- [x] Update test_worker_logging function to use loguru capture
- [x] Remove `logging.basicConfig` and related setup
- [x] Ensure log assertions work with loguru output format
- [x] Verify all existing tests still pass

### 4. Update requirements documentation
- [x] Modify the existing "Basic worker logging" requirement in add-worker-core/specs/worker-core/spec.md
- [x] Update requirement to reference loguru instead of standard logging

### 5. Validation and testing
- [x] Run all existing tests to ensure no regressions
- [x] Verify log output format is improved and readable
- [x] Test exception handling and traceback capture
- [x] Confirm backward compatibility with custom logger injection
- [x] Run `ruff` to ensure code style compliance

## Dependencies and Ordering

- **Task 1** must be completed first (dependency addition)
- **Task 2** is the core implementation and should be done before tests
- **Task 3** depends on Task 2 completion
- **Task 4** can be done in parallel with other tasks
- **Task 5** should be done last for final validation

## Validation Criteria

1. All existing tests pass without modification (except for logging-specific tests)
2. Log output is properly formatted with timestamps and structured information
3. Exception tracebacks are captured and formatted correctly
4. Worker constructor still accepts custom logger instances for backward compatibility
5. Project builds and installs correctly with new dependency
6. No runtime errors or import failures