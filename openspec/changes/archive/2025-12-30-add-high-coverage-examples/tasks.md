## 1. Example Suite
- [x] 1.1 Define example naming, ordering, and conventions
- [x] 1.2 Add `examples/README.md` explaining learning path and feature coverage
- [x] 1.3 Implement `examples/basic/01_end_to_end.py`
- [x] 1.4 Implement `examples/basic/02_eta_delayed_execution.py`
- [x] 1.5 Implement `examples/basic/03_bounded_concurrency.py`
- [x] 1.6 Implement `examples/basic/04_failures_and_tracebacks.py`
- [x] 1.7 Implement `examples/basic/05_sync_client_with_worker.py`

## 2. Documentation Integration
- [x] 2.1 Update `docs/quickstart.md` to reference `examples/basic/01_end_to_end.py`
- [x] 2.2 Add/adjust a docs page describing runnable examples and recommended order
- [x] 2.3 Ensure docs do not reference unimplemented example features as runnable

## 3. Validation
- [x] 3.1 Add `tests/validation/test_examples.py` to execute example scripts with timeouts
- [x] 3.2 Ensure example validation runs in default `pytest` invocation
- [x] 3.3 Fix or replace any existing example validation scripts that reference wrong paths

## 4. Review
- [x] 4.1 Confirm each example is clearly distinct and teaches one core feature
- [x] 4.2 Confirm examples use only public `sitq` APIs and run without external infra

