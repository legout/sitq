## ADDED Requirements

### Requirement: Documentation Layout Validation
The test suite SHALL validate that the documentation layout matches the approved Ditaxis structure.

#### Scenario: Validation enforces required docs entry points
- **WHEN** `pytest` is run
- **THEN** documentation validation tests SHALL assert that required portal and entry-point pages exist
- **AND** SHALL assert that the interactive notebook exists at `docs/tutorials/interactive-tutorial.ipynb`

### Requirement: Documentation Snippet Syntax Checking
The test suite SHALL validate that documentation code blocks are syntactically valid Python.

#### Scenario: Snippets remain parseable
- **WHEN** documentation validation tests run
- **THEN** Python code blocks in documentation SHALL be parsed successfully
