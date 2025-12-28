## MODIFIED Requirements

### Requirement: User Documentation Structure
The system SHALL provide comprehensive user documentation organized by user journey and complexity.

#### Scenario: Getting started content matches the implemented v1 API
- **WHEN** a new user follows the README or documentation quickstart
- **THEN** all referenced APIs and classes SHALL exist in the v1 code under `src/sitq/`
- **AND** the documented signatures SHALL match the implemented signatures
- **AND** the “Getting Started” path SHALL link to at least one runnable `examples/` script for first success

## ADDED Requirements

### Requirement: Documentation API Consistency
Documentation code examples SHALL not reference APIs or features that are not implemented in `src/sitq`, unless explicitly labeled as future/roadmap content.

#### Scenario: Reader encounters an example snippet
- **WHEN** a user reads a code snippet in the documentation
- **THEN** it SHALL be either runnable with the current version of sitq
- **OR** clearly labeled as conceptual/future content if it depends on unimplemented features
