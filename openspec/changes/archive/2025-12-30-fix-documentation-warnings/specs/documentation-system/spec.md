## MODIFIED Requirements
### Requirement: Documentation Infrastructure
The system SHALL provide a professional documentation site using MkDocs with Material theme and automatic API reference generation, with zero build warnings and complete navigation coverage.

#### Scenario: Documentation site access
- **WHEN** a user visits the documentation site
- **THEN** system SHALL present a modern, responsive interface with Material theme
- **AND** SHALL provide clear navigation and search functionality
- **AND** SHALL work on both desktop and mobile devices

#### Scenario: API reference generation
- **WHEN** documentation is built from source code
- **THEN** system SHALL automatically generate API reference from docstrings using mkdocstrings
- **AND** SHALL include type hints, parameter descriptions, and examples
- **AND** SHALL stay synchronized with code changes
- **AND** SHALL provide correct navigation entries for all API documentation files

#### Scenario: Documentation build process
- **WHEN** developers update documentation
- **THEN** system SHALL provide simple build commands
- **AND** SHALL validate documentation structure and links
- **AND** SHALL support local development and preview
- **AND** SHALL produce zero warnings and info messages about orphaned files or broken links

#### Scenario: Complete navigation coverage
- **WHEN** documentation is built
- **THEN** system SHALL include all documentation files in navigation structure
- **AND** SHALL not produce "orphaned file" warnings
- **AND** SHALL provide access to all API reference pages through navigation

#### Scenario: Working links across documentation
- **WHEN** a user navigates documentation
- **THEN** all API reference links SHALL resolve to correct sitq.*.md files
- **AND** all example file links SHALL resolve to files in /examples/ directory
- **AND** system SHALL not produce broken link warnings during build

#### Scenario: External directory references
- **WHEN** documentation links to files outside docs directory
- **THEN** system SHALL properly resolve absolute path references starting with /
- **AND** SHALL support watching external directories for live reload

### Requirement: Documentation API Consistency
Documentation code examples SHALL not reference APIs or features that are not implemented in `src/sitq`, unless explicitly labeled as future/roadmap content. All links in documentation SHALL resolve correctly without warnings.

#### Scenario: Reader encounters an example snippet
- **WHEN** a user reads a code snippet in the documentation
- **THEN** it SHALL be either runnable with the current version of sitq
- **OR** clearly labeled as conceptual/future content if it depends on unimplemented features

#### Scenario: User follows API links
- **WHEN** a user clicks an API reference link in documentation
- **THEN** the link SHALL resolve to the correct API documentation page
- **AND** SHALL not produce broken link warnings during build
- **AND** SHALL use proper file names (e.g., sitq.queue.md not queue.md)

#### Scenario: User follows example links
- **WHEN** a user clicks an example file link in documentation
- **THEN** the link SHALL resolve to the example file in the /examples/ directory
- **AND** SHALL not produce broken link warnings during build
- **AND** SHALL use absolute paths from docs root (/examples/basic/*.py)
