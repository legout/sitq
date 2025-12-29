## 1. Portal + installation
- [ ] 1.1 Rewrite `docs/index.md` as a Ditaxis portal linking to tutorials/how-to/reference/explanation and `examples/basic/`
- [ ] 1.2 Update `docs/installation.md` to require Python `>=3.13` and describe supported install paths

## 2. Tutorials
- [ ] 2.1 Add `docs/tutorials/quickstart.md` linking to `examples/basic/01_end_to_end.py`
- [ ] 2.2 Add `docs/tutorials/delayed-execution.md` linking to `examples/basic/02_eta_delayed_execution.py`
- [ ] 2.3 Add `docs/tutorials/concurrency.md` linking to `examples/basic/03_bounded_concurrency.py`
- [ ] 2.4 Add `docs/tutorials/failures.md` linking to `examples/basic/04_failures_and_tracebacks.py`
- [ ] 2.5 Move and rewrite the interactive notebook to `docs/tutorials/interactive-tutorial.ipynb`

## 3. How-to guides
- [ ] 3.1 Add `docs/how-to/run-worker.md`
- [ ] 3.2 Add `docs/how-to/get-results.md`
- [ ] 3.3 Add `docs/how-to/handle-failures.md`
- [ ] 3.4 Add `docs/how-to/sqlite-backend.md`
- [ ] 3.5 Add `docs/how-to/troubleshooting.md`

## 4. Explanation
- [ ] 4.1 Add `docs/explanation/architecture.md`
- [ ] 4.2 Add `docs/explanation/serialization.md`
- [ ] 4.3 Add `docs/explanation/limitations.md`

## 5. Reference
- [ ] 5.1 Add mkdocstrings stubs under `docs/reference/api/` for all public `sitq` exports
- [ ] 5.2 Update portal/tutorial/how-to pages to link into the reference where appropriate

## 6. Validation
- [ ] 6.1 Ensure examples and docs snippets reference only implemented `src/sitq/` APIs
- [ ] 6.2 Ensure `mkdocs build` succeeds with no dead links
