## 1. Implementation
- [ ] 1.1 Define a `Serializer` protocol with `dumps` and `loads` methods.
- [ ] 1.2 Implement `CloudpickleSerializer` using `cloudpickle.dumps` and `cloudpickle.loads`.
- [ ] 1.3 Update `TaskQueue` and `Worker` constructors to accept an optional `Serializer` and default to `CloudpickleSerializer`.
- [ ] 1.4 Add unit tests for serializer behavior and TaskQueue payload round-tripping.

