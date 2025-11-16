# Replace Standard Logging with Loguru

## Summary

Replace the standard Python `logging` module with `loguru` throughout the sitq codebase to provide better structured logging, easier configuration, and improved developer experience.

## Motivation

The current implementation uses Python's standard logging module, which requires verbose configuration and lacks modern features out of the box. Loguru offers:

- Simpler setup and configuration
- Better structured logging with automatic formatting
- Built-in exception handling and traceback capture
- Easier filtering and routing of log messages
- Better async support
- Automatic log rotation and compression

## Scope

This change will:
1. Add `loguru` as a project dependency
2. Replace all `import logging` statements with `from loguru import logger`
3. Update the Worker class to use loguru's logger
4. Update test files that configure logging
5. Modify the existing "Basic worker logging" requirement to reference loguru instead of standard logging

## Impact

- **Breaking change**: Minor - public API that accepts logging.Logger instances will need updating
- **Dependencies**: Adds loguru as a runtime dependency
- **Configuration**: Simplifies logging configuration for users
- **Compatibility**: Maintains the same logging behavior and levels

## Alternatives Considered

1. **Keep standard logging**: Works but requires more boilerplate
2. **Use structlog**: Good structured logging but more complex setup
3. **Custom logging wrapper**: Would add maintenance overhead

Loguru provides the best balance of simplicity and functionality for this project's needs.