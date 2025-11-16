## ADDED Requirements

### Requirement: Top-level public API exports
The `sitq` package SHALL expose a small, explicit public API surface from its top-level namespace.

#### Scenario: Import core types from sitq
- **WHEN** a user writes `from sitq import TaskQueue, SyncTaskQueue, Worker, Result`
- **THEN** all four names SHALL resolve successfully
- **AND** they SHALL refer to the canonical async TaskQueue, sync wrapper, Worker, and Result types used by the rest of the library

### Requirement: Keep internal modules private
Internal implementation modules (such as backends and serialization internals) SHALL NOT be treated as part of the stable public API surface in v1.

#### Scenario: Use internal modules directly
- **WHEN** a user imports symbols from internal modules such as `sitq.backends.sqlite` or `sitq.serialization`
- **THEN** this usage SHALL be considered unsupported for API stability purposes
- **AND** future versions MAY change these internal modules without being considered a breaking change to the v1 public API

