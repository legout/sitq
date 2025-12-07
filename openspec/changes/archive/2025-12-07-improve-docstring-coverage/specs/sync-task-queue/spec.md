## MODIFIED Requirements
### Requirement: Synchronous wrapper interface
The system SHALL provide a synchronous wrapper (`SyncTaskQueue`) that manages its own event loop for use in synchronous codebases with comprehensive documentation.

#### Scenario: Context manager usage
- **WHEN** a caller uses `SyncTaskQueue` as a context manager
- **THEN** it SHALL start event loop on entry and clean up on exit
- **AND** SHALL provide clear examples of proper usage patterns
- **AND** SHALL document thread safety considerations

#### Scenario: Error handling in sync context
- **WHEN** task execution fails in sync wrapper
- **THEN** system SHALL convert async exceptions to sync equivalents
- **AND** SHALL document error mapping and handling strategies
- **AND** SHALL provide examples of error recovery patterns

## ADDED Requirements
### Requirement: Sync vs Async Usage Guidance
The system SHALL provide clear documentation on when to use sync vs async APIs.

#### Scenario: Usage decision guidance
- **WHEN** a developer chooses between TaskQueue and SyncTaskQueue
- **THEN** documentation SHALL provide clear decision criteria
- **AND** SHALL explain performance implications of each approach
- **AND** SHALL include examples of appropriate use cases

#### Scenario: Migration patterns
- **WHEN** a developer migrates from sync to async code
- **THEN** documentation SHALL provide migration patterns and examples
- **AND** SHALL highlight common pitfalls and best practices
- **AND** SHALL show equivalent code patterns for both approaches