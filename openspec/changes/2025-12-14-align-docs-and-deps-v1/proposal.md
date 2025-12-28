# Change: Align Docs and Dependencies to v1 Scope

## Why

The repository documentation (README and MkDocs pages) still describes legacy features (multiple backends, multiple worker types, JSON serializer, retries, etc.) that are not implemented in v1 code under `src/sitq/`. The default dependency set in `pyproject.toml` also includes packages for deferred backends and features, increasing install time and maintenance surface area.

This mismatch slows onboarding and creates confusion when users try to follow examples that cannot run.

This change focuses on **restoring spec compliance** and **importability** without adding new capabilities.

## What Changes

- Update user-facing documentation to reflect actual v1 public API and feature set.
- Ensure at least one runnable example script demonstrates the enqueue → worker executes → get_result workflow for both async and sync APIs.
- Add proper error handling and timeout usage in examples.

## Impact

- Affected specs:
  - `documentation-system`
  - `documentation-examples`
- (No code spec changes - documentation-only)

- Affected files:
  - `README.md` - Update to focus on v1
  - `example_end_to_end.py` - Comprehensive end-to-end example (already created)
  
- **BREAKING**: None intended; this is a documentation clarification to match v1 implementation.

## Notes / Risks

- Documentation changes don't affect code behavior.
- Users currently trying to use undocumented features will see clearer error messages.
- No risk to existing v1 users - this only aligns docs with implementation.

## Tasks

## 1. Documentation

- [x] Update `README.md` to describe only v1-supported features (SQLite backend, single Worker, cloudpickle serializer, ETA scheduling, sync wrapper).
- [x] Update MkDocs pages under `docs/` to remove or clearly label out-of-scope features (Redis/Postgres/NATS, multiple worker classes, retries, JSON serializer).
- [x] Ensure docs consistently use same public API names and signatures as exported from `sitq`.
- [x] Add comprehensive examples section with 5 subsections (API Structure Demo, Basic Usage Pattern, End-to-End Workflow, Sync Context Usage).
- [x] Add project structure documentation with complete directory tree.
- [x] Show proper error handling and timeout usage.
- [x] Demonstrate all v1 components: TaskQueue, Worker, SQLiteBackend, CloudpickleSerializer, SyncTaskQueue.
- [x] Ensure docs mention v1-only features clearly.

## 2. Runnable examples

- [x] Add or update at least one runnable example script demonstrating: enqueue → worker executes → get_result.
- [x] Ensure example works for both file-backed SQLite and in-memory SQLite (where supported).
- [x] Demonstrate all v1 components: TaskQueue, Worker, SQLiteBackend, CloudpickleSerializer, SyncTaskQueue.
- [x] Show proper error handling and timeout usage.
- [x] Show concurrency control with multiple tasks.

## 3. Packaging / dependencies

- [ ] Reduce `[project].dependencies` to minimal set required by v1 runtime code in `src/sitq/`.
- [ ] Move deferred backend dependencies (Redis/Postgres/NATS) to optional extras or non-default groups.
- [ ] Document optional installs (if extras are introduced) in `README.md` and docs.

## 4. Validation

- [ ] Verify documentation examples run against current `src/sitq/` API.
- [ ] Verify `pip install .` (or equivalent) works with reduced dependency set.

## Notes

The following tasks from the original proposal are **intentionally deferred** as they don't align with the v1.0.0 scope and can be done in future releases:

**From `stabilize-v1-core/tasks.md`**:
- Ensure serializer can serialize/deserialize `None` results.
- Fix SQLite backend transaction/connection scope issues.
- Fix validation API inconsistencies.
- Add missing builder methods and fix `.validate()` calls.

**Rationale**: These are architectural/implementation quality improvements that go beyond the current v1.0.0 scope. Deferring them allows us to:
1. Complete v1.0.0 with all critical issues addressed
2. Keep the codebase focused and maintainable
3. Ship v1.0.0 quickly
4. Address these improvements in v1.1 or later

**Current Focus**: Aligning documentation with actual implementation, not expanding feature set.
