## 1. Specification
- [x] 1.1 Create a `public-api-core` spec that defines the small v1 public API surface for the `sitq` package.

## 2. Implementation
- [x] 2.1 Update `src/sitq/__init__.py` to export `TaskQueue`, `SyncTaskQueue`, `Worker`, and `Result` via `__all__`.
- [x] 2.2 Update the README with examples that import these symbols from the top-level `sitq` package.

## 3. Testing
- [x] 3.1 Add tests that import the public API (`from sitq import TaskQueue, SyncTaskQueue, Worker, Result`) and exercise a basic enqueue / worker / result flow.

