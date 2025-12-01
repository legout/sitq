# Design: Replace Logging with Loguru

## Architectural Considerations

### Current State
- The sitq codebase currently uses Python's standard `logging` module
- Logging is primarily used in the `Worker` class for lifecycle and task execution events
- Configuration follows standard logging patterns with logger instances per module

### Target State
- Replace all `logging` usage with `loguru` 
- Maintain the same log levels and message content
- Leverage loguru's built-in formatting and configuration benefits
- Ensure no breaking changes to public APIs

### Implementation Strategy

#### 1. Dependency Management
- Add `loguru` to `pyproject.toml` dependencies
- Remove any future need for `logging` configuration

#### 2. Code Migration
- Replace `import logging` with `from loguru import logger`
- Remove `logger = logging.getLogger(__name__)` patterns
- Update all logging calls to use loguru's simplified API
- Preserve existing log levels (debug, info, warning, error)

#### 3. Configuration Benefits
- Loguru provides sensible defaults out of the box
- Better exception handling and traceback formatting
- Colorized console output by default
- Structured logging capabilities for future enhancement

#### 4. Compatibility Considerations
- This is an internal implementation change
- No impact on public APIs
- Log messages and levels remain the same
- Only the formatting and configuration backend changes

### Benefits

1. **Developer Experience**: No boilerplate configuration needed
2. **Better Output**: Colorized, formatted logs by default
3. **Exception Handling**: Superior traceback formatting
4. **Future-Proof**: Built-in structured logging support
5. **Performance**: Optimized for async applications

### Risks and Mitigations

- **Risk**: Loguru might have different performance characteristics
- **Mitigation**: Loguru is designed for performance and widely used in production

- **Risk**: Different formatting might affect log parsing
- **Mitigation**: Loguru is highly configurable; formatting can be adjusted if needed

### Files to Modify

1. `pyproject.toml` - Add loguru dependency
2. `src/sitq/worker.py` - Replace logging imports and usage
3. `openspec/changes/add-worker-core/specs/worker-core/spec.md` - Update requirement reference

### Testing Strategy

- Verify all existing log messages are emitted correctly
- Test different log levels work as expected
- Ensure exception logging includes proper tracebacks
- Validate no functional regression in worker behavior