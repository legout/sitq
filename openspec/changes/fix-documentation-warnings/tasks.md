## 1. Navigation Structure Updates (mkdocs.yml)
- [x] 1.1 Add `docs/index.md` to nav as homepage
- [x] 1.2 Add `docs/tutorials/basic-concepts.md` to Tutorials section
- [x] 1.3 Add `docs/how-to/deployment.md` to Development subsection
- [x] 1.4 Add `docs/how-to/error-handling.md` to Core Operations subsection
- [x] 1.5 Add `docs/how-to/serialization.md` to Development subsection
- [x] 1.6 Add `docs/how-to/sync-wrapper.md` to Development subsection
- [x] 1.7 Add `docs/how-to/workers.md` to Core Operations subsection
- [x] 1.8 Verify API docs nav entry properly handles mkdocstrings directory structure
- [x] 1.9 Add `examples/` directory to `watch` configuration in plugins section

## 2. Fix Broken API Links (docs/how-to/workers.md)
- [x] 2.1 Find and replace `../reference/api/queue.md` → `../reference/api/sitq.queue.md` (2 instances)
- [x] 2.2 Find and replace `../reference/api/sync.md` → `../reference/api/sitq.sync.md` (1 instance)
- [x] 2.3 Find and replace `../reference/api/core.md` → `../reference/api/sitq.core.md` (2 instances)
- [x] 2.4 Verify all API link replacements are correct

## 3. Fix Broken Example Links (Tutorial Files)
- [x] 3.1 Fix `docs/tutorials/quickstart.md`: Update `../../examples/basic/01_end_to_end.py` → `/examples/basic/01_end_to_end.py`
- [x] 3.2 Fix `docs/tutorials/delayed-execution.md`: Update `../../examples/basic/02_eta_delayed_execution.py` → `/examples/basic/02_eta_delayed_execution.py`
- [x] 3.3 Fix `docs/tutorials/concurrency.md`: Update `../../examples/basic/03_bounded_concurrency.py` → `/examples/basic/03_bounded_concurrency.py`
- [x] 3.4 Fix `docs/tutorials/failures.md`: Update `../../examples/basic/04_failures_and_tracebacks.py` → `/examples/basic/04_failures_and_tracebacks.py`

## 4. Fix External Directory Reference (docs/tutorials/index.md)
- [x] 4.1 Update `examples/README.md` → `/examples/README.md`

## 5. Validation and Testing
- [x] 5.1 Run `mkdocs build` and verify zero warnings and info messages
- [x] 5.2 Run `mkdocs serve` and verify all navigation links work
- [x] 5.3 Click through all updated links in documentation to verify they resolve correctly
- [x] 5.4 Verify API reference pages are accessible from nav
- [x] 5.5 Verify example file links open the correct files
- [x] 5.6 Test local development with live reload on example files

## 6. Final Verification
- [x] 6.1 Document that all 34 warnings have been resolved - Verified: 0 warnings remain
- [x] 6.2 Document that all 19 orphaned files are now in nav - Verified: 0 orphaned files remain
- [x] 6.3 Confirm no broken links remain in documentation - Verified: 0 broken link warnings
- [x] 6.4 Run `openspec validate fix-documentation-warnings --strict`
