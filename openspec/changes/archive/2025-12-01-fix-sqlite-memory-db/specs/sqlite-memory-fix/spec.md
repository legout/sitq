# Specification: Fix SQLite In-Memory Database Issue

## ADDED Requirements

### Requirement: Shared connection for in-memory databases
The SQLite backend SHALL use a shared connection for in-memory databases to ensure all operations access the same database instance.

#### Scenario: In-memory database initialization
**GIVEN** a SQLiteBackend is created with `:memory:` database path
**WHEN** the backend is initialized
**THEN** a persistent connection SHALL be established and reused
**AND** all subsequent operations SHALL use this shared connection
**AND** tables SHALL be accessible across all backend methods

#### Scenario: In-memory database operations
**GIVEN** an initialized in-memory SQLite backend
**WHEN** tasks are enqueued, reserved, and completed
**THEN** all operations SHALL work on the same database instance
**AND** data SHALL be properly persisted across method calls
**AND** no "no such table" errors SHALL occur

#### Scenario: Connection lifecycle management
**GIVEN** a SQLiteBackend with in-memory database
**WHEN** the backend is closed
**THEN** the shared connection SHALL be properly closed
**AND** resources SHALL be cleaned up
**AND** subsequent operations SHALL fail gracefully

### Requirement: Maintain file database compatibility
The SQLite backend SHALL maintain existing behavior for file-based databases.

#### Scenario: File database operations
**GIVEN** a SQLiteBackend with file database path
**WHEN** database operations are performed
**THEN** behavior SHALL be identical to current implementation
**AND** performance SHALL not be degraded
**AND** connection management SHALL remain per-method

### Requirement: Connection pooling for performance
The SQLite backend SHALL implement efficient connection management for both database types.

#### Scenario: Concurrent operations
**GIVEN** multiple concurrent database operations
**WHEN** operations are executed
**THEN** in-memory databases SHALL use the shared connection safely
**AND** file databases SHALL use connection pooling if beneficial
**AND** thread safety SHALL be maintained

## MODIFIED Requirements

### Requirement: SQLite backend initialization (from add-backend-sqlite)
The SQLite backend SHALL initialize with proper connection management based on database type.

#### Scenario: Database type detection
**GIVEN** a SQLiteBackend constructor with database path
**WHEN** initialization is performed
**THEN** in-memory databases SHALL use shared connection strategy
**AND** file databases SHALL use existing per-method connection strategy
**AND** the choice SHALL be made automatically based on path

### Requirement: Resource cleanup (from add-backend-sqlite)
The SQLite backend SHALL properly clean up connections based on the strategy used.

#### Scenario: Backend cleanup
**GIVEN** a SQLiteBackend that is being closed
**WHEN** close() is called
**THEN** shared connections SHALL be closed for in-memory databases
**AND** any connection pools SHALL be drained for file databases
**AND** all resources SHALL be released properly