# Design: Replace Logging with Loguru

## Architecture Overview

This change replaces Python's standard logging module with loguru across the sitq codebase. The change is primarily focused on the Worker component and test infrastructure.

## Current State Analysis

### Existing Logging Usage
- `src/sitq/worker.py`: Uses standard logging for worker lifecycle and task execution events
- `tests/test_worker_core.py`: Configures standard logging for test capture and debugging

### Current Logger Interface
```python
# Current pattern
logger = logging.getLogger("sitq.worker")
logger.info("Worker started")
logger.error(f"Task failed: {error}")
```

## Target Design

### Loguru Integration
- Replace `import logging` with `from loguru import logger`
- Remove logger instance creation (loguru provides a global logger)
- Maintain the same log levels and message patterns
- Leverage loguru's built-in formatting and exception handling

### API Compatibility
- Update Worker constructor to accept optional logger parameter (for compatibility)
- Default to loguru's global logger when no custom logger provided
- Maintain the same logging behavior for consumers

### Test Integration
- Replace logging configuration in tests with loguru configuration
- Use loguru's capture mechanism for test assertions
- Maintain test coverage of logging functionality

## Implementation Strategy

### Phase 1: Dependency and Core Changes
1. Add loguru to pyproject.toml dependencies
2. Update Worker class to use loguru
3. Maintain backward compatibility in constructor

### Phase 2: Test Updates
1. Update test files to use loguru
2. Ensure log capture and assertions work correctly
3. Verify all existing logging tests pass

### Phase 3: Documentation Updates
1. Update the "Basic worker logging" requirement
2. Update any documentation that references logging configuration

## Benefits

1. **Simplified Setup**: No need for logger configuration boilerplate
2. **Better Output**: Automatic formatting, colors, and structured output
3. **Exception Handling**: Built-in exception capture with better tracebacks
4. **Performance**: Optimized for async applications
5. **Extensibility**: Easy to add sinks, filters, and custom formatting

## Migration Considerations

- **Backward Compatibility**: The Worker constructor will still accept a logger parameter but will default to loguru
- **Configuration**: Users who currently configure logging will need to switch to loguru configuration
- **Testing**: Test utilities that rely on logging capture will need updates

## Risk Assessment

- **Low Risk**: Loguru is a well-maintained, widely-used library
- **Minimal Breaking Changes**: Only affects users with custom logging configuration
- **Easy Rollback**: Changes are isolated to logging statements