# Replace Logging with Loguru

## Summary

Replace the built-in Python `logging` module with `loguru` throughout the sitq codebase to provide better structured logging, easier configuration, and improved developer experience.

## Why

The current implementation uses Python's standard `logging` module, which requires boilerplate configuration and lacks modern features like structured logging out of the box. `loguru` offers:

- Simpler configuration (no boilerplate needed)
- Better structured logging with automatic parsing
- Colorized console output by default
- Easier exception handling and traceback formatting
- Built-in rotation and compression
- Better async support

## Motivation

## Scope

This change will:
1. Add `loguru` as a project dependency
2. Replace all `logging` imports and usage with `loguru`
3. Update existing logging requirements to reference loguru instead
4. Ensure all existing log levels and messages are preserved
5. Update any relevant documentation

## Files Affected

- `src/sitq/worker.py` - Main logging usage location
- `pyproject.toml` - Add loguru dependency
- `openspec/changes/add-worker-core/specs/worker-core/spec.md` - Update logging requirement
- Any future modules that might use logging

## Backwards Compatibility

This is an internal implementation change that does not affect public APIs. The logging behavior and messages will remain the same, just with better formatting and configuration options.

## Testing

- Verify all existing log messages are still emitted at correct levels
- Test loguru configuration works as expected
- Ensure no regression in worker functionality
- Validate structured logging output if applicable