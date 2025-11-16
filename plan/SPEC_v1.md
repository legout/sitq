# sitq v1 – Technical Specification

This document specifies the technical design for `sitq` v1, aligned with the v1 PRD. It focuses on a minimal, async‑first core with a single backend (SQLite) and a single worker abstraction, while keeping clear extension points for future features.

## 1. Architecture Overview

High‑level layers:

- **Public API**
  - `TaskQueue` (async)
  - `SyncTaskQueue` (sync wrapper)
- **Core**
  - Task orchestration, scheduling logic (ETA only), result handling.
- **Worker**
  - `Worker` class responsible for polling the backend, executing tasks, and recording results.
- **Backend**
  - `Backend` interface.
  - `SQLiteBackend` v1 implementation.
- **Serialization**
  - Single internal serializer (e.g. `CloudpickleSerializer`) hidden behind a small interface.

## 2. Core Data Models

### 2.1 Task Payload

Canonical in‑memory representation (Python object):

```python
TaskPayload = dict[str, Any]  # canonical keys:
# {
#   "func": Callable | str,  # callable or import path
#   "args": tuple,
#   "kwargs": dict,
#   "context": dict | None,  # optional, for future extension
# }
```

In v1:

- `func` may be stored as a callable in memory and serialized via the serializer.
- `context` is a simple optional dictionary for future context propagation; v1 keeps usage minimal.

### 2.2 Result Model

`Result` (public) is a lightweight data object returned to users:

```python
class Result:
    task_id: str
    status: Literal["pending", "success", "failed"]
    value: bytes | None       # serialized return value
    error: str | None         # error message
    traceback: str | None     # formatted traceback
    enqueued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
```

Backend stores a representation compatible with this model (e.g. columns in SQLite).

## 3. Public API Surface

### 3.1 Async TaskQueue

Module: `sitq.queue` (example, actual module name can follow existing layout).

```python
class TaskQueue:
    def __init__(
        self,
        backend: Backend | None = None,
        serializer: Serializer | None = None,
        *,
        default_result_timeout: float | None = None,
    ) -> None: ...

    async def enqueue(
        self,
        func: Callable[..., Any],
        *args: Any,
        eta: datetime | None = None,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str: ...

    async def get_result(
        self,
        task_id: str,
        timeout: float | None = None,
    ) -> Result | None: ...

    async def close(self) -> None: ...

    async def __aenter__(self) -> "TaskQueue": ...
    async def __aexit__(self, exc_type, exc, tb) -> None: ...
```

Behavior:

- `backend`:
  - Defaults to `SQLiteBackend` with a sensible default DB path (e.g. `sitq.db`) if not provided.
- `serializer`:
  - Defaults to the internal cloudpickle‑based serializer.
- `enqueue`:
  - Creates a `task_id` (e.g. UUID4 string).
  - Wraps `func`, `args`, `kwargs`, and optional `context` into a canonical payload.
  - Persists the task via backend with:
    - `task_id`
    - serialized payload
    - `enqueued_at`
    - `available_at` = `eta` or `now`
    - initial status = `pending`
- `get_result`:
  - Optionally waits up to `timeout` seconds, polling backend periodically.
  - Returns `Result` instance or `None` if not ready or not found.

### 3.2 SyncTaskQueue

Module: `sitq.sync`.

```python
class SyncTaskQueue:
    def __init__(
        self,
        backend: Backend | None = None,
        serializer: Serializer | None = None,
        *,
        default_result_timeout: float | None = None,
    ) -> None: ...

    def __enter__(self) -> "SyncTaskQueue": ...
    def __exit__(self, exc_type, exc, tb) -> None: ...

    def enqueue(
        self,
        func: Callable[..., Any],
        *args: Any,
        eta: datetime | None = None,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str: ...

    def get_result(
        self,
        task_id: str,
        timeout: float | None = None,
    ) -> Result | None: ...
```

Implementation notes:

- `SyncTaskQueue` internally owns an event loop:
  - Creates and runs an `asyncio` event loop in a dedicated thread or in the main thread, depending on the chosen pattern.
  - Uses this loop to delegate to `TaskQueue` methods.
- Constraints:
  - Intended for synchronous scripts and environments without a pre‑existing event loop.
  - Async applications should prefer `TaskQueue` directly.

## 4. Backend Interface and SQLite Backend

### 4.1 Backend Interface

Module: `sitq.backends.base`.

```python
class Backend(Protocol):
    async def connect(self) -> None: ...
    async def close(self) -> None: ...

    async def enqueue(
        self,
        task_id: str,
        payload: bytes,
        available_at: datetime,
    ) -> None: ...

    async def reserve(
        self,
        *,
        max_items: int,
        now: datetime,
    ) -> list["ReservedTask"]: ...

    async def mark_success(
        self,
        task_id: str,
        result_value: bytes,
        *,
        finished_at: datetime,
    ) -> None: ...

    async def mark_failure(
        self,
        task_id: str,
        error: str,
        traceback: str,
        *,
        finished_at: datetime,
    ) -> None: ...

    async def get_result(self, task_id: str) -> Result | None: ...
```

`ReservedTask`:

```python
class ReservedTask:
    task_id: str
    payload: bytes
    enqueued_at: datetime
```

Semantics:

- `reserve`:
  - Returns up to `max_items` tasks whose `available_at <= now` and are currently `pending`.
  - Must atomically transition tasks to an “in progress” state to avoid multi‑worker duplication.
- `mark_success` / `mark_failure`:
  - Update status, store serialized result or error/traceback, and timestamps.

### 4.2 SQLiteBackend

Module: `sitq.backends.sqlite`.

Schema (conceptual):

- `tasks` table:
  - `task_id` TEXT PRIMARY KEY
  - `status` TEXT CHECK(status IN ('pending', 'in_progress', 'success', 'failed'))
  - `payload` BLOB NOT NULL
  - `enqueued_at` TIMESTAMP WITH TIME ZONE NOT NULL
  - `available_at` TIMESTAMP WITH TIME ZONE NOT NULL
  - `started_at` TIMESTAMP WITH TIME ZONE
  - `finished_at` TIMESTAMP WITH TIME ZONE
  - `result_value` BLOB
  - `error` TEXT
  - `traceback` TEXT

Key implementation points:

- Use WAL mode for better concurrency where available.
- `reserve`:
  - Implement atomically with a transaction:
    - Select up to `max_items` rows with `status = 'pending'` and `available_at <= now`.
    - Update them to `status = 'in_progress'` and set `started_at`.
  - Return `ReservedTask` instances for selected rows.
- `mark_success` / `mark_failure`:
  - Update status and relevant fields.
- `get_result`:
  - Return a `Result` constructed from the row, or `None` if not found.

## 5. Worker

Module: `sitq.worker`.

### 5.1 Public API

```python
class Worker:
    def __init__(
        self,
        backend: Backend,
        serializer: Serializer,
        *,
        max_concurrency: int = 10,
        poll_interval: float = 1.0,
        batch_size: int = 10,
    ) -> None: ...

    async def start(self) -> None: ...
    async def stop(self) -> None: ...
```

### 5.2 Behavior

- `start`:
  - Connects to backend (if not already connected).
  - Starts an internal loop:
    - While not stopped:
      - Acquire up to `max_concurrency - current_running` new tasks via `reserve`.
      - For each reserved task:
        - Acquire semaphore.
        - Spawn an `asyncio` task to execute the job:
          - Deserialize payload.
          - Execute callable (async or sync; sync via `run_in_executor`).
          - On success: serialize result, call `mark_success`.
          - On exception: capture error and traceback, call `mark_failure`.
          - Release semaphore.
      - If no tasks reserved:
        - Sleep for `poll_interval` (or use simple backoff).
- `stop`:
  - Signal the loop to stop polling.
  - Wait for all in‑flight tasks (semaphore acquisition ensures we can track them).

### 5.3 Error Handling

- Worker must:
  - Log exceptions and keep running unless they are fatal (e.g. unrecoverable DB errors).
  - Avoid crashing on individual task failures; failures are recorded via `mark_failure`.

## 6. Serialization

Module: `sitq.serialization`.

### 6.1 Serializer Interface

```python
class Serializer(Protocol):
    def dumps(self, obj: Any) -> bytes: ...
    def loads(self, data: bytes) -> Any: ...
```

### 6.2 Default Implementation

- `CloudpickleSerializer` (name can follow existing conventions):
  - Uses `cloudpickle.dumps` / `cloudpickle.loads`.
- v1 does **not** expose a public registration mechanism; advanced pluggability is future work.

## 7. Scheduling & Time Semantics

- All datetimes in public APIs and storage are:
  - Timezone‑aware.
  - Represented internally as UTC.
- `eta`:
  - When provided, stored as `available_at`.
  - Worker only reserves tasks where `available_at <= now`.
- No cron / recurring scheduling in v1.

## 8. Reliability & Concurrency Semantics

- **Delivery model**:
  - At‑least‑once: tasks may run more than once if a worker crashes after marking them in progress but before marking success/failure.
  - v1 may accept some limited duplication; more advanced retry and deduplication logic can be added later.
- **Concurrency**:
  - Limited via semaphore in `Worker`.
  - Backend `reserve` and state transitions ensure that multiple workers do not execute the same task concurrently under normal operation.
- **Shutdown**:
  - `stop` prevents new reservations and waits for in‑flight tasks to complete.

## 9. Observability & Logging

- Minimal logging via standard library `logging`:
  - Worker start/stop.
  - Task reserved, started, completed, failed (at info or debug level).
  - Backend connection errors.
- This layer doubles as a natural extension point for a future event system (e.g. structured events emitted in addition to logs).

## 10. Extension Points (Post‑v1)

Design considerations to keep future work straightforward:

- **Backends**:
  - `Backend` interface should be stable and generic enough to support Redis, Postgres, NATS, etc.
- **Worker types**:
  - Execution of the callable is isolated so alternative strategies (process pools, gevent) can be introduced in dedicated worker subclasses or strategies without changing `TaskQueue`.
- **Event system**:
  - Logging calls can be wrapped or mirrored with an event dispatcher in a future version.
- **Serializers**:
  - The `Serializer` protocol allows adding a registration/configuration mechanism later.
- **Scheduling**:
  - The `eta`/`available_at` mechanism maps naturally to a separate cron scheduler that enqueues tasks with future `eta` values.

