## ADDED Requirements

### Requirement: Documentation Portal Landing Page
The documentation site SHALL provide a portal landing page that routes readers to the correct Diataxis section and runnable examples.

#### Scenario: Reader chooses a documentation path
- **WHEN** a user opens the documentation landing page
- **THEN** it SHALL link to Tutorials, How-to Guides, Reference, and Explanation
- **AND** it SHALL link to at least one runnable example under `examples/basic/`

### Requirement: Installation Documentation Accuracy
Installation documentation SHALL match the project's published runtime requirements and supported installation methods.

#### Scenario: Reader installs sitq
- **WHEN** a user follows the installation instructions
- **THEN** the documented Python requirement SHALL be `>=3.13`
- **AND** the documented install commands SHALL not reference non-existent extras

## MODIFIED Requirements

### Requirement: Documentation API Consistency
Documentation code examples SHALL not reference APIs or features that are not implemented in `src/sitq`.

#### Scenario: Reader encounters an example snippet
- **WHEN** a user reads a code snippet in the documentation
- **THEN** it SHALL be runnable with the current version of sitq
- **AND** it SHALL not depend on unimplemented features
