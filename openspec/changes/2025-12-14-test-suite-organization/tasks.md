## 1. Structure

- [x] Create `tests/` directory structure with clear separation:
   - `tests/unit/`
   - `tests/integration/`
   - `tests/performance` (benchmarks; opt-in)
- [x] Move existing root-level tests into the appropriate directories.

## 2. Pytest behavior

- [x] Ensure default `pytest` run excludes benchmarks/performance tests.
- [x] Provide an explicit way to run performance tests (e.g., marker `performance`).
- [x] Document how to run unit vs integration vs performance test subsets.

## 3. Cleanup

- [ ] Convert "script-style tests" that return booleans / print output into proper pytest assertions.
- [x] Ensure tests import `sitq` via consistent paths (prefer `import sitq` with `PYTHONPATH=src` in test config).

## 4. Validation

- [ ] Run default pytest suite (unit+integration) and confirm it completes quickly.
- [ ] Run performance tests explicitly and confirm they still work.

