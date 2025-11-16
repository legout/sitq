# Project Context

## Purpose

`sitq` (Simple Task Queue) is a lightweight, async‑first Python task queue library for running background jobs in small‑to‑medium services and tools.  

The project’s goals:
- Provide a simple, **async‑first** API for enqueueing and processing tasks.
- Offer an embedded, file‑backed queue that works out of the box (SQLite).
- Keep the core small and understandable, while leaving clear hooks for more advanced capabilities (multiple backends, worker types, events, cron) in later versions.
- Support both async and sync applications via an async core plus a minimal sync wrapper.

The codebase is currently in a **refactor towards a simplified v1**:
- `src_bak/` contains the previous, more feature‑rich implementation (multiple backends, multiple workers, retries, context propagation).
- `PRD_v1.md` and `SPEC_v1.md` describe the lean v1 scope and are the primary source of truth for new work.

## Tech Stack

- Language / Runtime: **Python 3.13+**, async‑first (`asyncio`).
- Packaging / Build:
  - `pyproject.toml` with `uv_build` as the build backend.
  - `uv` / standard Python packaging workflows.
- Persistence / Backends:
  - **v1 target**: `SQLiteBackend` using SQLite for file‑backed persistence.
  - Legacy / planned: Postgres, Redis, NATS backends (see `src_bak/`), to be reintroduced as future capabilities.
- Data access and drivers:
  - `sqlalchemy`, `aiosqlite`, `asyncpg`, `aioredis`, `nats-py`.
- Serialization:
  - `cloudpickle` as the primary serializer (v1).
  - A JSON‑compatible serializer exists in `src_bak` and may return later as an optional alternative.
- Scheduling / time:
  - Datetimes are UTC and timezone‑aware.
  - `croniter` is available for future cron/recurring scheduling but is **not** part of v1’s core behavior.
- Tooling:
  - `ruff` for linting (and formatting via `ruff format` if desired).
  - `marimo`, `ipython` and small scripts under `dev/` and `playground.py` for experiments.

## Project Conventions

### Code Style

- Python 3.13+ with type hints on public APIs.
- Follow PEP 8 style and modern Python idioms (dataclasses where appropriate, explicit imports, clear naming).
- Prefer small, focused modules with explicit `__all__` for exported symbols.
- Use `ruff` to enforce linting and code style; run it before committing.
- Public APIs should have short docstrings describing intent and key parameters.

### Architecture Patterns

- **Async‑first core**:
  - All core components (`TaskQueue`, `Backend`, `Worker`) are asynchronous and built around `asyncio`.
  - Sync support is provided via a thin `SyncTaskQueue` wrapper over the async API.
- **Layered design**:
  - Public API layer: `TaskQueue`, `SyncTaskQueue`, `Worker`.
  - Core orchestration: task enqueueing, ETA scheduling, result handling.
  - Backend layer: `Backend` interface plus `SQLiteBackend` implementation in v1.
  - Serialization layer: internal `Serializer` protocol with a cloudpickle implementation.
- **Canonical task and result models**:
  - Tasks use a canonical envelope containing `func`, `args`, `kwargs`, and optional `context`.
  - Results use a unified `Result` object with `status`, `value`, `error`, `traceback`, and timestamps.
- **Reliability model**:
  - At‑least‑once delivery; no global ordering guarantees.
  - Workers are expected to be idempotent where possible.
- **Refactor state**:
  - New code should follow `SPEC_v1.md` and treat `src_bak/` as reference material only, not as the source of truth.

### Testing Strategy

- Target testing stack:
  - **pytest** for unit and integration tests (to be formalized as the refactor progresses).
  - Tests should cover `TaskQueue`, `Worker`, and the `SQLiteBackend` end‑to‑end.
- Approach:
  - Unit tests for serialization, backend behavior (enqueue/reserve/mark_success/mark_failure/get_result).
  - Integration tests for worker loops (concurrency, ETA scheduling, failure handling).
  - Example‑driven tests derived from the README and design examples where useful.
- Current state:
  - Automated tests are not yet fully established; new contributions should add tests alongside code and move the project toward a standard pytest layout (`tests/` with clear separation between unit and integration tests).

### Git Workflow

- Repository:
  - Main branch (e.g. `main`/`master`) is the source of truth for released behavior.
- OpenSpec‑driven changes:
  - For new capabilities, breaking changes, or larger refactors, create an OpenSpec change under `openspec/changes/<change-id>/` following `openspec/AGENTS.md`.
  - Use verb‑led, kebab‑case change IDs (e.g. `add-sqlite-backend`, `refactor-worker-loop`).
- Branching:
  - Create feature branches per change (e.g. `feature/add-sqlite-backend`, `refactor/worker-loop`).
  - Keep branches small and focused on a single change-id when possible.
- Commits:
  - Prefer descriptive commit messages that reference the relevant change-id (e.g. `add-sqlite-backend: implement reserve/mark_success`).
  - Keep commits logically grouped (tests + implementation together where practical).

## Domain Context

- Domain: background job processing / task queues for Python services.
- Typical tasks:
  - I/O‑bound work (HTTP calls, emails, file uploads).
  - Short CPU‑bound jobs where a simple process or thread‑based worker is sufficient.
  - Delayed tasks scheduled to run at or after a specific time.
- Usage models:
  - Small services running a few worker processes against a shared SQLite DB.
  - Future support for external backends (Redis, Postgres, NATS) for more distributed setups.
- Semantics:
  - At‑least‑once execution; callers must treat handlers as idempotent where failure or retry is possible.
  - No strict ordering guarantees between tasks; use application‑level coordination if ordering matters.

## Important Constraints

- Technical:
  - Python 3.13+ only (per `pyproject.toml`).
  - Async‑first design; sync usage is via wrappers and should not leak into the core.
  - v1 limits the **official** backend surface to SQLite, even though legacy code for other backends exists in `src_bak/`.
- Architectural:
  - Keep the v1 core small and easily testable; advanced features should not complicate the core implementation.
  - New capabilities should be spec‑driven via OpenSpec where they affect behavior or public APIs.
- Backwards compatibility:
  - The project is still early (0.x); minor breaking changes are acceptable when justified and captured via OpenSpec.
- Non‑goals:
  - Strong distributed guarantees (exactly‑once, strict ordering) are out of scope.
  - Massive, multi‑region deployments and highly exotic workloads are not primary targets.

## External Dependencies

- Runtime:
  - SQLite database file for the default backend.
  - Future: Postgres, Redis, and NATS instances for their respective backends (once reintroduced).
- Python libraries:
  - `sqlalchemy`, `aiosqlite`, `asyncpg`, `aioredis`, `nats-py`, `cloudpickle`, `croniter`, `greenlet`.
- Tools:
  - `uv` for building and dependency management (via `uv_build`).
  - `ruff` for linting/formatting.
- No third‑party SaaS services are required by default; external queues, brokers, or DB instances only come into play when using non‑SQLite backends in the future.
