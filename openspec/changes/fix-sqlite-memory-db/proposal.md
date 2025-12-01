# Change Proposal: Fix SQLite In-Memory Database Issue

## Problem Statement

The current SQLite backend implementation has a critical issue with in-memory databases (`:memory:`). In SQLite, each connection to `:memory:` creates a completely separate database instance. This causes the following problems:

1. **Schema initialization fails**: The `initialize()` method creates tables in one connection, but `enqueue()` uses a different connection that doesn't see the tables
2. **Data isolation**: Different methods cannot share data when using in-memory databases
3. **Testing failures**: Tests using `:memory:` fail with "no such table" errors
4. **Development friction**: Developers cannot use in-memory databases for quick testing

## Root Cause

SQLite's `:memory:` database implementation creates a new database for each connection. The current backend architecture creates separate connections for:
- Database initialization (`initialize()`)
- Task operations (`enqueue()`, `reserve()`, `mark_success()`, etc.)

Since these are different connections, they don't share the same in-memory database.

## Proposed Solution

### Option 1: Shared Cache Connection (Preferred)
Implement a persistent connection pool for in-memory databases that shares connections across all backend operations.

### Option 2: File-Based Fallback
Automatically detect `:memory:` usage and fall back to a temporary file database.

### Option 3: Connection Management
Refactor to use a single persistent connection per backend instance.

## Technical Requirements

### Requirement: Maintain in-memory database support
The SQLite backend SHALL support `:memory:` databases for testing and development.

#### Scenario: In-memory database initialization
**GIVEN** a SQLiteBackend is created with `:memory:` database path
**WHEN** the backend is initialized
**THEN** all subsequent operations SHALL see the same database schema and data
**AND** tables SHALL be accessible across all backend methods

#### Scenario: In-memory database operations
**GIVEN** an initialized in-memory SQLite backend
**WHEN** tasks are enqueued, reserved, and completed
**THEN** all operations SHALL work on the same database instance
**AND** data SHALL be properly persisted across method calls

### Requirement: Preserve existing API
The fix SHALL maintain backward compatibility with existing SQLiteBackend API.

#### Scenario: API compatibility
**GIVEN** existing code using SQLiteBackend
**WHEN** the fix is applied
**THEN** all existing method signatures SHALL remain unchanged
**AND** existing behavior for file databases SHALL be preserved

### Requirement: Performance considerations
The solution SHALL maintain or improve performance characteristics.

#### Scenario: Performance impact
**GIVEN** the fixed SQLite backend
**WHEN** benchmarked against the current implementation
**THEN** performance SHALL be equivalent or better
**AND** memory usage SHALL be reasonable for in-memory databases

## Implementation Approach

### Phase 1: Connection Management
1. Add connection pooling for in-memory databases
2. Implement persistent connection management
3. Ensure proper cleanup on backend close

### Phase 2: Testing and Validation
1. Add comprehensive tests for in-memory database scenarios
2. Validate integration with TaskQueue and Worker
3. Performance benchmarking

### Phase 3: Documentation
1. Update documentation with in-memory database usage notes
2. Add examples and best practices
3. Document any limitations or considerations

## Success Criteria

1. ✅ All existing tests pass with file databases
2. ✅ New tests pass with in-memory databases  
3. ✅ Integration tests work with both database types
4. ✅ Performance is maintained or improved
5. ✅ No breaking changes to public API

## Risk Assessment

### Low Risk
- API changes (none planned)
- File database behavior (should be unchanged)

### Medium Risk  
- Connection management complexity
- Memory usage for in-memory databases
- Thread safety considerations

### Mitigation Strategies
- Comprehensive testing of both database types
- Memory usage monitoring
- Thread-safe connection pooling
- Gradual rollout with fallback options

## Alternatives Considered

1. **Disable in-memory support**: Rejected - would break existing usage patterns
2. **Force file databases**: Rejected - reduces flexibility for testing
3. **Use shared cache**: Selected - maintains compatibility while fixing the issue

## Dependencies

- None - this is a self-contained fix to the SQLite backend
- Should be implemented before any integration testing improvements