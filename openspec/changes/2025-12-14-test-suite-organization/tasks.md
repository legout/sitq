## 1. Structure

- [ ] Create `tests/` directory structure with clear separation:
  - `tests/unit/`
  - `tests/integration/`
  - `tests/performance/` (benchmarks; opt-in)
- [ ] Move existing root-level tests into the appropriate directories.

## 2. Pytest behavior

- [ ] Ensure default `pytest` run excludes benchmarks/performance tests.
- [ ] Provide an explicit way to run performance tests (e.g. marker `performance`).
- [ ] Document how to run unit vs integration vs performance test subsets.

## 3. Cleanup

- [ ] Convert “script-style tests” that return booleans / print output into proper pytest assertions.
- [ ] Ensure tests import `sitq` via consistent paths (prefer `import sitq` with `PYTHONPATH=src` in test config).

## 4. Validation

- [ ] Run the default pytest suite (unit+integration) and confirm it completes quickly.
- [ ] Run performance tests explicitly and confirm they still work.

