## 1. Documentation

- [x] Update `README.md` to describe only v1-supported features (SQLite backend, single Worker, cloudpickle serializer, ETA scheduling, sync wrapper).
- [x] Update MkDocs pages under `docs/` to remove or clearly label out-of-scope features (Redis/Postgres/NATS, multiple worker classes, retries, JSON serializer).
- [x] Ensure docs consistently use the same public API names and signatures as exported from `sitq`.
- [x] Add comprehensive examples section with 5 subsections (API Structure Demo, Basic Usage Pattern, End-to-End Workflow, Sync Context Usage).
- [x] Add project structure documentation with complete directory tree.
- [x] Show proper error handling and timeout usage.
- [x] Demonstrate all v1 components: TaskQueue, Worker, SQLiteBackend, CloudpickleSerializer, SyncTaskQueue.
- [x] Show concurrency control with multiple tasks.

## 2. Runnable examples

- [x] Ensure at least one runnable example script demonstrates: enqueue → worker executes → get_result.
- [x] Ensure example works for both file-backed SQLite and in-memory SQLite (where supported).
- [x] Demonstrate all v1 components: TaskQueue, Worker, SQLiteBackend, CloudpickleSerializer, SyncTaskQueue.
- [x] Show proper error handling and timeout usage.
- [x] Show concurrency control with multiple tasks.

## 3. Packaging / dependencies

- [x] Reduce `[project].dependencies` to minimal set required by v1 runtime code in `src/sitq/`.
- [x] Move deferred backend dependencies (Redis/Postgres/NATS) to optional extras or non-default groups.
- [x] Document optional installs (if extras are introduced) in `README.md` and docs.
- [x] Verify `pip install .` (or equivalent) works with reduced dependency set.

## 4. Validation

- [x] Verify `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -c "import sitq"` succeeds.
- [x] Run a minimal end-to-end example (enqueue → worker processes → get_result) for both async and sync APIs.

## Notes

Tasks from the "stabilize-v1-core" proposal related to task failures and connection scope are intentionally deferred as they don't block the v1.0.0 release. These can be addressed in a future proposal.

All critical P0 and P1 issues from the code review have been addressed. The codebase is now in a good state for v1.0.0 release.
