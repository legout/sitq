## 1. Implementation
- [ ] 1.1 Implement `SyncTaskQueue` as a context manager that owns an internal asyncio event loop.
- [ ] 1.2 Delegate `enqueue` and `get_result` to the async `TaskQueue` using the internal loop.
- [ ] 1.3 Document usage constraints and examples in docstrings and the README.
- [ ] 1.4 Add tests for basic synchronous enqueue/get_result flows.

