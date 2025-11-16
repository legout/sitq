## 1. Implementation
- [x] 1.1 Define a `Serializer` protocol with `dumps` and `loads` methods.
- [x] 1.2 Implement `CloudpickleSerializer` using `cloudpickle.dumps` and `cloudpickle.loads`.
- [x] 1.3 Update `TaskQueue` and `Worker` constructors to accept an optional `Serializer` and default to `CloudpickleSerializer`.
- [x] 1.4 Add unit tests for serializer behavior and TaskQueue payload round-tripping.

