## MODIFIED Requirements

### Requirement: Example Code Quality
All basic examples SHALL follow high code quality standards and be immediately runnable.

#### Scenario: Example runs against the v1 package install
- **WHEN** a user installs `sitq` and runs the provided “first example”
- **THEN** the example SHALL run without errors using only v1-supported features
- **AND** it SHALL not require external infrastructure beyond SQLite

#### Scenario: Example uses only public sitq APIs
- **WHEN** a user copies the example’s code into their own project
- **THEN** it SHALL use only public `sitq` APIs
- **AND** it SHALL avoid references to unimplemented features
