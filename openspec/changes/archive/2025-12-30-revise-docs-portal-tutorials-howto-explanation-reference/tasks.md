## 1. Portal + installation
- [x] 1.1 Rewrite `docs/index.md` as a Diätaxis portal linking to tutorials/how-to/reference/explanation and `examples/basic/`
- [x] 1.2 Update `docs/installation.md` to require Python `>=3.13` and describe supported install paths

## 2. Tutorials
- [x] 2.1 Add `docs/tutorials/quickstart.md` linking to `examples/basic/01_end_to_end.py`
- [x] 2.2 Add `docs/tutorials/delayed-execution.md` linking to `examples/basic/02_eta_delayed_execution.py`
- [x] 2.3 Add `docs/tutorials/concurrency.md` linking to `examples/basic/03_bounded_concurrency.py`
- [x] 2.4 Add `docs/tutorials/failures.md` linking to `examples/basic/04_failures_and_tracebacks.py`
- [x] 2.5 Move and rewrite the interactive notebook to `docs/tutorials/interactive-tutorial.ipynb`

## 3. How-to guides
- [x] 3.1 Add `docs/how-to/run-worker.md`
- [x] 3.2 Add `docs/how-to/get-results.md`
- [x] 3.3 Add `docs/how-to/handle-failures.md`
- [x] 3.4 Add `docs/how-to/sqlite-backend.md`
- [x] 3.5 Add `docs/how-to/troubleshooting.md`

## 4. Explanation
- [x] 4.1 Add `docs/explanation/architecture.md`
- [x] 4.2 Add `docs/explanation/serialization.md`
- [x] 4.3 Add `docs/explanation/limitations.md`

## 5. Reference
- [x] 5.1 Add mkdocstrings stubs under `docs/reference/api/` for all public `sitq` exports
- [x] 5.2 Update portal/tutorial/how-to pages to link into the reference where appropriate

## 6. Validation
- [x] 6.1 Ensure examples and docs snippets reference only implemented `src/sitq/` APIs
- [x] 6.2 Ensure `mkdocs build` succeeds with no dead links
