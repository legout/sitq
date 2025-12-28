## MODIFIED Requirements

### Requirement: Method error handling (from all existing proposals)
All existing methods SHALL be updated with proper error handling and validation.

#### Scenario: SyncTaskQueue wraps operational failures in domain exceptions
- **GIVEN** `SyncTaskQueue.enqueue` or `SyncTaskQueue.get_result` delegates to the async core
- **WHEN** an operational failure occurs (backend error, serialization error, timeout misconfiguration)
- **THEN** the sync wrapper SHALL raise a sitq domain exception (a subclass of `SitqError`)
- **AND** it SHALL preserve the original exception as the cause

