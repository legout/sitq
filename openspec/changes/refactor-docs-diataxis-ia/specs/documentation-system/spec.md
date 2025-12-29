## ADDED Requirements

### Requirement: Ditaxis Information Architecture
The documentation site SHALL be organized into four distinct sections: Tutorials, How-to Guides, Reference, and Explanation.

#### Scenario: Reader navigates by intent
- **WHEN** a user opens the documentation site navigation
- **THEN** the top-level navigation SHALL include Tutorials, How-to Guides, Reference, and Explanation
- **AND** each page SHALL belong to exactly one of these sections

### Requirement: MkDocs Navigation Integrity
The documentation build configuration SHALL not reference missing documentation pages.

#### Scenario: Documentation build has no dead nav entries
- **WHEN** the documentation site is built
- **THEN** `mkdocs build` SHALL succeed
- **AND** the configured navigation SHALL not reference files that do not exist

### Requirement: Repository Metadata Consistency
The documentation site configuration SHALL point to the authoritative sitq repository.

#### Scenario: Repo link points to current repo
- **WHEN** a user clicks the repository link in the documentation UI
- **THEN** it SHALL point to `https://github.com/legout/sitq`
