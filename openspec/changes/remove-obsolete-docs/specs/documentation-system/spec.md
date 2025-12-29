## ADDED Requirements

### Requirement: Obsolete Documentation Removal
The documentation set SHALL not contain pages that document unimplemented APIs or speculative features.

#### Scenario: Legacy pages are removed after replacements exist
- **WHEN** documentation is refactored to a new information architecture
- **THEN** obsolete pages SHALL be removed once their replacements exist
- **AND** the documentation navigation SHALL not link to removed pages
- **AND** removed pages SHALL not be archived in-repo
