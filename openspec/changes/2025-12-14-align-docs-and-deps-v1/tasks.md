## 1. Documentation

- [ ] Update `README.md` to describe only v1-supported features (SQLite backend, single Worker, cloudpickle serializer, ETA scheduling, sync wrapper).
- [ ] Update MkDocs pages under `docs/` to remove or clearly label out-of-scope features (Redis/Postgres/NATS, multiple worker classes, retries, JSON serializer).
- [ ] Ensure docs consistently use the same public API names and signatures as exported from `sitq`.

## 2. Runnable examples

- [ ] Add or update at least one runnable example script demonstrating: enqueue → worker executes → get_result.
- [ ] Ensure the example works for both file-backed SQLite and in-memory SQLite (where supported).

## 3. Packaging / dependencies

- [ ] Reduce `[project].dependencies` to the minimal set required by v1 runtime code in `src/sitq/`.
- [ ] Move deferred backend dependencies (Redis/Postgres/NATS) to optional extras or non-default groups.
- [ ] Document optional installs (if extras are introduced) in `README.md` and docs.

## 4. Validation

- [ ] Verify documentation examples run against the current `src/sitq` API.
- [ ] Verify `pip install .` (or equivalent) works with the reduced dependency set.

