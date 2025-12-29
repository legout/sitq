## MODIFIED Requirements

### Requirement: Default cloudpickle serializer
The system SHALL provide a default cloudpickle-based serializer implementation that conforms to the `Serializer` protocol.

#### Scenario: Serialize None result value
- **WHEN** a task callable returns `None`
- **THEN** the system SHALL serialize `None` as a valid result payload
- **AND** `TaskQueue` / `Worker` SHALL be able to deserialize it back to `None`

