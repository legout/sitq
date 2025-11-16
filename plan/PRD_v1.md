# sitq v1 – Product Requirements Document (PRD)

## 1. Summary

`sitq` v1 is a **minimal, async‑first Python task queue** focused on:

- Simple API for enqueuing and executing background tasks.
- A single, reliable, default backend (SQLite) suitable for local and small‑scale deployments.
- A single worker model with configurable concurrency.
- A small, explicit surface area that is easy to understand, test, and extend in later versions.

This v1 intentionally **defers advanced features** (multiple backends, multiple worker types, event system, rich context propagation, cron scheduling) to keep the initial release small, stable, and easy to evolve.

## 2. Problem & Motivation

Existing task queue solutions (e.g. Celery, RQ, Dramatiq) can be:

- Overly complex for small services and libraries.
- Opinionated about infrastructure (requiring Redis/RabbitMQ).
- Hard to integrate cleanly with modern `asyncio` applications.

We want a **lightweight, async‑first queue** that:

- Works well for small to medium Python services.
- Is easy to reason about and debug.
- Provides a solid foundation that can grow into more advanced capabilities later.

## 3. Target Users & Use Cases

### 3.1 Target Users

- Python developers building async applications (FastAPI, Starlette, etc.).
- Library or tool authors who need a simple background task runner.
- Developers who want an embedded, file‑backed queue for local or small‑scale production workloads.

### 3.2 Core Use Cases

- Offloading I/O‑bound work (sending emails, calling APIs, file uploads, etc.).
- Running short CPU‑bound tasks in the background in low‑traffic scenarios.
- Scheduling a task to run at or after a specific time (simple ETA scheduling).
- Local development and testing of background jobs without external infrastructure.

## 4. Goals (v1)

- **Async‑first API**
  - Provide an `async` `TaskQueue` as the primary interface.
- **Optional sync wrapper**
  - Provide a minimal, well‑documented `SyncTaskQueue` for synchronous code, with clear constraints.
- **Single default backend**
  - Ship with a single, production‑capable backend: **SQLite**.
  - Support multiple worker processes reading from the same SQLite database for basic scaling.
- **Single worker abstraction**
  - Provide one worker type (`Worker`) with configurable concurrency and graceful shutdown.
- **Basic scheduling**
  - Support immediate execution and optional `eta` (UTC datetime) for “run at or after this time”.
- **Unified result model**
  - Standard `Result` object with clear fields (`status`, `value`, `error`, `traceback`, timestamps).
- **Predictable semantics**
  - Document reliability model (e.g. at‑least‑once delivery) and expectations around idempotency.
- **Small, coherent API surface**
  - Keep public APIs small and stable; prefer adding capabilities via configuration and optional modules in later versions.

## 5. Non‑Goals / Out of Scope for v1

The following are **explicitly out of scope** for v1 and should be treated as **future enhancements**:

- **Additional backends**
  - Redis, Postgres, NATS, RabbitMQ, Kafka, in‑memory clusters, etc.
- **Additional worker types**
  - Dedicated `ProcessWorker`, `ThreadWorker`, `GeventWorker`, etc., as separate public classes.
- **Event system**
  - General event bus / hooks system (e.g. `on_task_enqueued`, `on_task_started`, `on_task_completed`, `on_task_failed`) beyond minimal logging.
- **Cron / recurring scheduling**
  - Cron‑style periodic scheduling and complex recurrence rules.
- **Advanced context propagation**
  - Rich DI frameworks, automatic tracing integration, or generic context wrapper abstractions beyond a minimal mechanism.
- **Pluggable serializers**
  - Public plug‑in API for serializers; v1 uses a single built‑in serializer.
- **High‑availability / partition tolerance guarantees**
  - Strong distributed guarantees beyond basic multi‑worker, single‑backend usage.
- **Multi‑tenant / multi‑queue routing**
  - Named queues, priorities, routing keys, and sharding.

These non‑goals should still influence design (e.g. keep extension points in mind) but must **not** complicate the v1 implementation.

## 6. Functional Requirements

### 6.1 Async TaskQueue API

- Provide an `async` `TaskQueue` class with:
  - `enqueue(func, *args, eta: datetime | None = None, **kwargs) -> str`
    - Enqueues a callable and its arguments.
    - Returns a `task_id` string.
    - Optional `eta` (timezone‑aware UTC datetime) for delayed execution.
  - `get_result(task_id: str, timeout: float | None = None) -> Result | None`
    - Waits for a task result up to `timeout` seconds, or returns `None` if not completed in time.
  - `close()` / `__aexit__`
    - Cleanly closes connections to the backend.
- The async API is the **canonical** interface; all other APIs delegate to it.

### 6.2 Sync TaskQueue Wrapper

- Provide a `SyncTaskQueue` as a **convenience wrapper** around `TaskQueue`:
  - Usable as a context manager: `with SyncTaskQueue(...) as queue: ...`
  - Blocking `enqueue` and `get_result` methods that internally run the async versions.
- Document constraints clearly:
  - Designed for use in environments **without** an existing event loop.
  - In async environments (e.g. FastAPI request handlers), users should use the async API directly.

### 6.3 Worker

- Provide a `Worker` component that:
  - Polls the backend for available tasks.
  - Executes tasks with a concurrency limit (`max_concurrency`).
  - Handles graceful shutdown (finish in‑flight tasks, stop polling).
- Requirements:
  - Concurrency limited via `asyncio.Semaphore` or equivalent.
  - Backoff strategy for empty queue (configurable base delay).
  - Logging of task start, completion, and failure.
  - Configurable polling interval and batch size.

### 6.4 Backend (SQLite)

- Ship a `SQLiteBackend` that:
  - Stores tasks and results in a local SQLite database file.
  - Supports multiple worker processes interacting with the same DB when correctly configured.
- Functional capabilities:
  - Create tables on first use (or migration step).
  - Enqueue tasks with:
    - `task_id`
    - serialized payload (including callable reference and args)
    - `available_at` timestamp (for `eta` scheduling)
    - status fields (`pending`, `in_progress`, `success`, `failed`)
  - Atomically reserve tasks for workers (e.g. via row locking or status transitions).
  - Persist results, including success value or error metadata.
  - Query results by `task_id`.

### 6.5 Serialization

- v1 uses a **single built‑in serializer**, e.g. `cloudpickle`‑based:
  - Must support serializing typical Python callables, args, and kwargs.
  - Should be encapsulated behind a simple internal interface to keep future pluggability possible.
- No public plug‑in system for serializers in v1.

### 6.6 Result Model

- Provide a unified `Result` object that includes:
  - `task_id: str`
  - `status: Literal["pending", "success", "failed"]`
  - `value: bytes | None` (serialized return value, on success)
  - `error: str | None` (error message, on failure)
  - `traceback: str | None` (formatted stack trace, on failure)
  - `enqueued_at: datetime`
  - `started_at: datetime | None`
  - `finished_at: datetime | None`
- `get_result` should return a `Result` instance or `None` if not found or not ready within timeout.

### 6.7 Scheduling Semantics

- Immediate tasks:
  - `eta is None` ⇒ task is eligible for execution as soon as a worker sees it.
- Delayed tasks:
  - `eta` is a timezone‑aware UTC datetime; task becomes eligible when `eta <= now`.
- No cron / recurring scheduling in v1.

### 6.8 Reliability & Semantics

- Explicitly document:
  - **Delivery semantics**: at‑least‑once delivery (tasks may run more than once in rare failure scenarios).
  - **Ordering**: no global ordering guarantees; workers may pick tasks in any order subject to backend implementation.
  - **Idempotency**: applications should treat task handlers as idempotent where possible.
- Worker and backend must handle:
  - Process crashes during task execution (tasks can be retried on next worker run).
  - Safe shutdown, avoiding new reservations while allowing in‑flight tasks to finish.

## 7. Non‑Functional Requirements

- **Python versions**: Support currently targeted Python versions (e.g. 3.10+; exact range to be confirmed in spec).
- **Performance**:
  - Adequate for small to medium workloads on a single host.
  - Reasonable overhead for enqueueing (< few ms) and result retrieval.
- **Resource usage**:
  - Bounded concurrency via configuration.
  - No unbounded in‑memory queues; persistence through SQLite.
- **Observability**:
  - Basic logging for key events (startup, shutdown, task lifecycle).
  - Clear error messages where possible.

## 8. UX & API Considerations

- Strive for **small, intuitive APIs**:
  - `TaskQueue` and `Worker` should expose only the most essential methods.
  - Use sensible defaults (e.g. default SQLite path, default serializer).
- Examples in documentation:
  - Basic async usage with `TaskQueue` and `Worker`.
  - Basic sync usage with `SyncTaskQueue`.
  - Simple delayed task with `eta`.

## 9. Future Enhancements (Post‑v1 Roadmap)

These features should **not** influence v1 implementation complexity beyond keeping obvious extension points:

- **Additional backends**: Redis, Postgres, NATS, RabbitMQ, in‑memory.
- **Additional worker types**: Process‑based, gevent‑based, dedicated thread worker classes, etc.
- **Event system**:
  - Extensible hooks (e.g. `on_task_enqueued`, `on_task_started`, `on_task_retried`, `on_task_completed`, `on_task_failed`).
  - Integration with logging/metrics/tracing.
- **Cron / recurring scheduling**:
  - A separate scheduler component or library that translates cron expressions into `eta` tasks.
- **Pluggable serializers**:
  - Public registration API for custom serializers.
- **Context propagation improvements**:
  - More ergonomic helpers for `contextvars`, logging, tracing, and dependency injection.

## 10. Success Metrics

- Developer feedback:
  - APIs are perceived as easy to understand and integrate.
- Adoption:
  - Usable for small internal services without additional infrastructure.
- Stability:
  - No data corruption in the SQLite backend under normal operating conditions.
  - Predictable behavior under typical error scenarios (worker crash, task exceptions).

