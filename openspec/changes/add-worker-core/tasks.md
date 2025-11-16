## 1. Implementation
- [ ] 1.1 Implement a `Worker` class that uses a backend and serializer to execute reserved tasks.
- [ ] 1.2 Add concurrency control using an `asyncio.Semaphore` and a main polling loop.
- [ ] 1.3 Implement graceful shutdown that stops polling and waits for in-flight tasks to finish.
- [ ] 1.4 Add logging for worker start/stop and task start/completion/failure events.
- [ ] 1.5 Add integration tests covering basic execution, ETA scheduling, and failure recording.

