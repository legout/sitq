# Sitq: Refactoring Documentation

This document provides comprehensive documentation for the `sitq` project, covering the design decisions, key changes, and architectural improvements made during the recent refactoring process.

## 1. Project Overview

`sitq` (Simple Task Queue) is a lightweight, async-first Python task queue designed for efficient, non-blocking I/O and better resource utilization. It provides a robust, extensible, and maintainable foundation for asynchronous task processing.

### Core Components and Interactions:

*   **TaskQueue API (Async and Sync)**: The primary interface for users to enqueue tasks and retrieve results. It offers both asynchronous and synchronous methods, with the latter acting as wrappers managing an internal event loop.
*   **Async Core Logic**: The central orchestrator, responsible for task serialization, scheduling, and result handling. It coordinates communication between the `TaskQueue`, backends, and workers.
*   **Backend Interface**: An abstract interface defining how `sitq` interacts with various data stores (e.g., SQLite, Redis, NATS). This pluggable design allows for easy integration of new persistence layers.
*   **Worker Interface**: Defines the execution strategy for tasks. Different worker implementations (`AsyncWorker`, `ThreadWorker`, `ProcessWorker`) cater to diverse workload types.
*   **Context Wrapper**: A crucial mechanism for propagating `contextvars` (like logging or tracing) from the enqueueing application to the worker executing the task, ensuring context preservation across different execution environments.
*   **Data Store**: The underlying persistence layer (e.g., SQLite, Redis, Postgres, NATS) where tasks and results are stored.

## 2. Architectural Overview

The refined `sitq` architecture is built upon an **async-first** principle, leveraging Python's `asyncio` for high performance and scalability. Synchronous operations are provided as convenient wrappers around this asynchronous core. This modular structure emphasizes clear separation of concerns, enhancing maintainability and extensibility.

### Key Architectural Elements:

*   **Async-First Design**: The core `TaskQueue`, `Backend`, and `Worker` components are fully asynchronous, enabling efficient handling of concurrent I/O-bound operations.
*   **Synchronous Wrappers**: For ease of use and integration with existing synchronous codebases, `TaskQueue` and other public APIs offer synchronous counterparts. These wrappers manage an internal `asyncio` event loop.
*   **Context Propagation**: `contextvars` are captured at the time of task enqueueing and restored during worker execution, ensuring that contextual information (e.g., user IDs, request IDs) is preserved across `async`, `thread`, and `process` boundaries. This is facilitated by `cloudpickle` serialization of the context.
*   **Modular Structure**:
    *   **TaskQueue API**: The public-facing entry point for task management.
    *   **Async Core**: Handles the fundamental logic of task processing, independent of specific backends or worker types.
    *   **Pluggable Backend Interface**: Allows for diverse data storage solutions.
    *   **Pluggable Worker Interface**: Supports various execution models (async, thread, process).

## 3. Key Changes and Improvements

### Concurrency Model

Concurrency limits are now correctly enforced for workers through the use of `asyncio.Semaphore` within the `Worker` class (`src/sitq/workers/base.py`). When tasks are fetched, the worker attempts to claim them. Upon successful claiming, a semaphore is acquired *before* launching the task processing, and it is released only after processing completes. This ensures that the number of concurrently executing tasks never exceeds the configured limit, preventing resource exhaustion and maintaining system stability.

### Canonical Payload Contract

The task envelope structure has been standardized to a dictionary containing `func`, `args`, and `kwargs`. This canonical form simplifies backend implementations by providing a consistent serialized payload.

*   **Serialization**: `cloudpickle` is the default serializer, capable of handling complex Python objects, including closures and dynamically created classes. A `JsonSerializer` is also available, which converts callables to import path strings (`module.function_name`) for JSON compatibility, and resolves them upon deserialization.
*   **Binary Data Handling**: Backends like Redis and NATS handle binary data (e.g., serialized functions or context) safely by encoding it as Base64 strings before storage and decoding it upon retrieval. This ensures compatibility with text-based data stores.
    *   Refer to `src/sitq/queue.py` for task enqueueing and serialization of the canonical envelope.
    *   Refer to `src/sitq/serializers.py` for `PickleSerializer` and `JsonSerializer` implementations.
    *   Refer to backend files (`src/sitq/backends/sqlite.py`, `src/sitq/backends/redis.py`, `src/sitq/backends/nats.py`) for how they handle task data and result serialization/deserialization, including Base64 encoding for binary payloads where necessary.

### Unified Result Model

The new approach to task results ensures that only one final result per task ID is recorded and retrieved. This prevents premature visibility of intermediate or partial results. The `Worker` (`src/sitq/workers/base.py`) now explicitly sets a `result_id` on the task only when it reaches a terminal state (success or terminal failure). Backend `get_result` methods (`src/sitq/backends/sqlite.py`, `src/sitq/backends/redis.py`, `src/sitq/backends/nats.py`) are designed to retrieve results based on this `result_id`, guaranteeing that only the final, definitive outcome is returned to the user. This improves result consistency and reliability.

### Worker Synchronicity

Workers are now explicitly defined for their synchronicity:

*   **`ThreadWorker` (`src/sitq/workers/thread.py`)**: Designed for synchronous, I/O-bound functions, executing them in a `ThreadPoolExecutor`. The main event loop remains unblocked while the task runs in a separate thread.
*   **`ProcessWorker` (`src/sitq/workers/process.py`)**: Intended for synchronous, CPU-bound functions, executing them in a `ProcessPoolExecutor`. This isolates CPU-intensive tasks to separate processes, preventing them from blocking the event loop or other workers.
*   **`AsyncWorker` (`src/sitq/workers/async_.py`)**: For native asynchronous functions, executing them directly within the event loop.
*   **`run_async_sync()` Helper (`src/sitq/workers/async_.py`)**: Provides a synchronous wrapper to execute asynchronous callables from synchronous code. If an event loop is already running, it spawns a new event loop in a separate thread to run the async function, blocking until completion. This is crucial for integrating `sitq` into mixed synchronous/asynchronous applications.

### Context Propagation

A robust mechanism for capturing and restoring `contextvars` (e.g., `logging.Logger`, `opentelemetry.trace.Span`) has been implemented to ensure context is preserved across task enqueueing and worker execution, regardless of the worker type (`async`, `thread`, or `process`).

*   **Capture at Enqueue**: When a task is enqueued (`src/sitq/queue.py`), the current `contextvars.Context` is captured using `contextvars.copy_context()` and `cloudpickle.dumps()` for serialization. This serialized context is stored as part of the `Task` object (`src/sitq/core.py`).
*   **Restoration at Execution**: In each worker type (`AsyncWorker`, `ThreadWorker`, `ProcessWorker`), the serialized context is deserialized (`cloudpickle.loads()`) and restored using `context.run()` before the task function is executed.
    *   `src/sitq/queue.py`: Shows how context is captured during `enqueue`.
    *   `src/sitq/core.py`: Defines the `context` field in the `Task` dataclass.
    *   `src/sitq/workers/base.py`: The `_process` method handles deserialization and passing the context to `_execute`.
    *   `src/sitq/workers/async_.py`, `src/sitq/workers/thread.py`, `src/sitq/workers/process.py`: Implement the `_execute` method, explicitly running the task function within the restored context. For `ProcessWorker`, `cloudpickle` is used to serialize and deserialize the context across process boundaries.

## 4. Design Rationale

The major design decisions were driven by the need for performance, scalability, and developer experience:

*   **Async-First for Performance and Scalability**: By building the core on `asyncio`, `sitq` can handle a large number of concurrent I/O-bound tasks with minimal overhead. This non-blocking approach is crucial for high-throughput applications.
*   **Synchronous Wrappers for Developer Experience**: Recognizing that not all applications are fully asynchronous, synchronous wrappers were introduced to provide a familiar interface. This allows developers to leverage `sitq`'s powerful async capabilities without rewriting their entire codebase, easing adoption.
*   **Pluggable Backends and Serializers**: This design choice ensures maximum flexibility and extensibility. Users can choose the best persistence layer and serialization format for their specific needs, and new implementations can be easily added without modifying the core library.

## 5. Extensibility

The new architecture significantly enhances `sitq`'s extensibility, making it straightforward to add new components:

*   **New Backends**: To add a new backend (e.g., RabbitMQ, Kafka), one simply needs to create a new class inheriting from `sitq.backends.base.Backend` and implement its well-defined asynchronous methods (e.g., `enqueue`, `fetch_due_tasks`, `store_result`). The modular interface abstracts away the underlying data store specifics.
*   **New Worker Types**: Custom worker types can be introduced by inheriting from `sitq.workers.base.Worker` and implementing the `_execute` method. This allows for diverse execution strategies, such as workers integrating with different concurrency models (e.g., `gevent` or `Trio`).
*   **New Features**: The modular and interface-driven design facilitates the addition of new features. New functionalities can be implemented as separate components that interact with existing ones through their defined APIs, minimizing coupling and promoting maintainability. For example, a task chaining feature could be implemented by coordinating task enqueuing and result retrieval via the `TaskQueue` API.

## 6. Usage Examples

**(Note: This section will be updated with actual code examples demonstrating the new features, including context propagation and different worker types. For now, refer to the `README.md` for basic usage.)**

### Basic Usage (SQLite Backend)

```python
import asyncio
from sitq import TaskQueue, AsyncWorker, SQLiteBackend, PickleSerializer
import contextvars

# Define a context variable
my_context_var = contextvars.ContextVar('my_context_var', default='default_value')

# 1. Define your async task function
async def say_hello(name: str):
    current_context_value = my_context_var.get()
    print(f"Hello, {name} with context: {current_context_value}")
    return f"Greetings, {name} from worker with context: {current_context_value}!"

async def main():
    # 2. Set up the queue with a backend and serializer
    queue = TaskQueue(
        backend=SQLiteBackend(db_path="example_queue.db"),
        serializer=PickleSerializer()
    )

    # 3. Connect to the backend
    await queue.backend.connect()

    # Set context before enqueuing
    my_context_var.set('enqueued_context')

    # 4. Enqueue a task and get its ID
    task_id = await queue.enqueue(say_hello, "World")
    print(f"Task {task_id} enqueued.")

    # Reset context (to demonstrate propagation)
    my_context_var.set('main_loop_context')

    # 5. Start a worker to process the task
    worker = AsyncWorker(
        backend=queue.backend,
        serializer=PickleSerializer(),
        concurrency=5
    )

    # Run the worker for a short period to process the task
    await worker.start()
    await asyncio.sleep(1) # Allow time for the task to be processed
    await worker.stop()

    # 6. Retrieve the result
    result = await queue.get_result(task_id, timeout=5)
    if result:
        print(f"Result received: {result.status}")
        if result.status == "success":
            value = queue.serializer.loads(result.value)
            print(f"Task return value: {value}")
    else:
        print("Did not receive result in time.")

    # 7. Clean up
    await queue.backend.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Running a Worker for a CPU-Bound Task (ProcessWorker)

```python
import asyncio
import time
from sitq import TaskQueue, ProcessWorker, SQLiteBackend, PickleSerializer
import contextvars

# Define a context variable
my_process_context_var = contextvars.ContextVar('my_process_context_var', default='default_process_value')

# A CPU-bound function that uses context
def compute_fibonacci_with_context(n):
    current_context_value = my_process_context_var.get()
    print(f"Computing Fibonacci({n}) in process with context: {current_context_value}")
    if n <= 1:
        return n
    else:
        return compute_fibonacci_with_context(n-1) + compute_fibonacci_with_context(n-2)

async def main():
    queue = TaskQueue(
        backend=SQLiteBackend("cpu_tasks.db"),
        serializer=PickleSerializer()
    )
    await queue.backend.connect()

    # Set context before enqueuing
    my_process_context_var.set('enqueued_process_context')

    # Use ProcessWorker to run the sync function in a separate process
    worker = ProcessWorker(
        backend=queue.backend,
        serializer=PickleSerializer(),
        concurrency=2 # Run up to 2 CPU-bound tasks in parallel
    )

    await worker.start()

    print("Enqueuing CPU-bound task...")
    task_id = await queue.enqueue(compute_fibonacci_with_context, 35)

    # Reset context (to demonstrate propagation)
    my_process_context_var.set('main_loop_process_context')

    result = await queue.get_result(task_id, timeout=20)
    if result and result.status == 'success':
        value = queue.serializer.loads(result.value)
        print(f"Fibonacci result: {value}")
    else:
        print(f"Task failed or timed out. Status: {result.status if result else 'timeout'}")

    await worker.stop()
    await queue.backend.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Using the Synchronous Wrapper (`SyncTaskQueue`)

```python
from sitq import SyncTaskQueue, SQLiteBackend, PickleSerializer
from sitq.workers.async_ import run_async_sync
import contextvars

# Define a context variable
my_sync_context_var = contextvars.ContextVar('my_sync_context_var', default='default_sync_value')

def add_with_context(x, y):
    current_context_value = my_sync_context_var.get()
    print(f"Adding {x} and {y} in synchronous task with context: {current_context_value}")
    return x + y

async def run_worker_in_background(queue):
    worker = AsyncWorker(backend=queue.backend, serializer=queue.serializer)
    await worker.start()
    await asyncio.sleep(2) # Give worker time to process
    await worker.stop()

# The SyncTaskQueue manages the event loop internally
# Set context before enqueuing
my_sync_context_var.set('enqueued_sync_context')

with SyncTaskQueue(
    backend=SQLiteBackend("sync_queue.db"),
    serializer=PickleSerializer()
) as queue:
    task_id = queue.enqueue(add_with_context, 5, 10)
    print(f"Task {task_id} enqueued.")

    # Reset context (to demonstrate propagation)
    my_sync_context_var.set('main_sync_loop_context')

    # In a real application, you'd run workers in a separate process or persistent background service.
    # For this example, we'll run a worker briefly in the background.
    run_async_sync(run_worker_in_background, queue)

    result = queue.get_result(task_id, timeout=5)
    if result and result.status == 'success':
        value = queue.serializer.loads(result.value)
        print(f"Addition result: {value}")
    else:
        print(f"Task failed or timed out. Status: {result.status if result else 'timeout'}")

```

## 7. Future Considerations/Roadmap

*   **Timezone Consistency**: Implement timezone-aware scheduling across all backends to prevent discrepancies.
*   **Backend-Specific Fixes**: Address specific scheduling or result handling nuances for Postgres and NATS backends to ensure full feature parity and robustness.
*   **Comprehensive Testing**: Expand test coverage, particularly for edge cases, error handling, and concurrency scenarios, to ensure the stability and reliability of the refactored system.
*   **Advanced Scheduling**: Explore more sophisticated scheduling options beyond simple `cron`-like expressions, such as recurring tasks based on intervals or specific events.
*   **Monitoring and Observability**: Integrate with common monitoring tools (e.g., Prometheus, OpenTelemetry) for better visibility into task queues, worker performance, and error rates.
*   **Distributed Locking Enhancements**: Improve distributed locking mechanisms for high-concurrency and fault-tolerant environments.
*   **Pluggable Retry Policies**: Allow for more flexible and custom retry policies.