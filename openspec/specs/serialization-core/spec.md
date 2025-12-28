# serialization-core Specification

## Purpose
TBD - created by archiving change add-serialization-core. Update Purpose after archive.
## Requirements
### Requirement: Serializer protocol
The system SHALL define an internal `Serializer` protocol for encoding and decoding Python objects used in task payloads and results.

#### Scenario: Serialize arbitrary payload
- **WHEN** a task payload containing a callable, positional arguments, and keyword arguments is passed to the serializer
- **THEN** the serializer SHALL return a `bytes` value suitable for storage in the backend

#### Scenario: Deserialize arbitrary payload
- **WHEN** previously serialized task payload bytes are passed to the serializer
- **THEN** the serializer SHALL return a Python object equivalent to the original payload

### Requirement: Default cloudpickle serializer
The system SHALL provide a default cloudpickle-based serializer implementation that conforms to the `Serializer` protocol.

#### Scenario: Serialize None result value
- **WHEN** a task callable returns `None`
- **THEN** the system SHALL serialize `None` as a valid result payload
- **AND** `TaskQueue` / `Worker` SHALL be able to deserialize it back to `None`

### Requirement: Non-pluggable public API
The system SHALL NOT expose a public plug-in mechanism for custom serializers in v1.

#### Scenario: No serializer registration API
- **WHEN** a user inspects the public API of the library
- **THEN** they SHALL NOT find any configuration hooks for registering custom serializers beyond passing an explicit internal serializer instance where supported

