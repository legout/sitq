# Change: Add internal serializer abstraction and default cloudpickle implementation

## Why
sitq v1 needs a single, internal serializer to encode task payloads and results while keeping room for future pluggable serializers without exposing them publicly.

## What Changes
- Introduce a `serialization-core` capability describing a minimal `Serializer` protocol with `dumps` and `loads`.
- Specify a default `CloudpickleSerializer` implementation used by `TaskQueue`, `Worker`, and the backend.
- Clarify that v1 does not expose a pluggable serializer registration mechanism in the public API.

## Impact
- Affected specs: `serialization-core`, `task-queue-core` (uses the serializer)
- Affected code: `src/sitq/serialization.py`, serializer wiring in `src/sitq/queue.py` and `src/sitq/worker.py`

