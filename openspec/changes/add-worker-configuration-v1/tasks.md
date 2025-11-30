## 1. Specification
- [x] 1.1 Update `worker-core` spec to describe the Worker constructor parameters (`max_concurrency`, `poll_interval`, `batch_size`) and their defaults.
- [x] 1.2 Add requirements that define how the Worker combines `max_concurrency`, the current number of running tasks, and `batch_size` when calling `backend.reserve`.

## 2. Implementation
- [x] 2.1 Update the `Worker` constructor in `src/sitq/worker.py` to match the specified configuration parameters and defaults.
- [x] 2.2 Adjust the Worker polling loop to compute how many tasks can be reserved as `min(batch_size, max_concurrency - running_count)` and pass that to `backend.reserve`.

## 3. Testing
- [x] 3.1 Extend Worker tests to cover different combinations of `max_concurrency` and `batch_size`, ensuring the number of concurrent tasks never exceeds `max_concurrency`.
- [x] 3.2 Run the full Worker test suite to confirm behavior matches the updated specification.

