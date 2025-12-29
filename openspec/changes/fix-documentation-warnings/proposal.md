# Change: Fix documentation build warnings and improve nav structure

## Why

The MkDocs documentation build currently produces 34 warnings and 19 info messages that degrade documentation quality and user experience. These include:
- 8 broken API links in documentation files
- 4 broken example file links  
- 19 orphaned documentation files not in navigation
- 2 nav configuration warnings
- 1 external directory reference issue

These issues prevent users from accessing complete documentation, create confusion with broken links, and reduce the professional quality of the documentation site.

## What Changes

### 1. Navigation Structure Updates (mkdocs.yml)
- Add all orphaned docs to nav configuration
  - `docs/index.md` - Main project index
  - `docs/tutorials/basic-concepts.md` - Tutorial content
  - `docs/how-to/deployment.md` - Deployment guide
  - `docs/how-to/error-handling.md` - Error handling guide
  - `docs/how-to/serialization.md` - Serialization guide
  - `docs/how-to/sync-wrapper.md` - Sync wrapper guide
  - `docs/how-to/workers.md` - Worker guide
  - Auto-generated API docs in `reference/api/`
- Properly structure API docs nav entry for mkdocstrings

### 2. Fix Broken API Links (docs/how-to/workers.md)
- Update `../reference/api/queue.md` → `../reference/api/sitq.queue.md`
- Update `../reference/api/sync.md` → `../reference/api/sitq.sync.md`
- Update `../reference/api/core.md` → `../reference/api/sitq.core.md`
- Affects 8 link references across the file

### 3. Fix Broken Example Links (4 tutorial files)
- `docs/tutorials/quickstart.md`: Update `../../examples/basic/01_end_to_end.py` → `/examples/basic/01_end_to_end.py`
- `docs/tutorials/delayed-execution.md`: Update `../../examples/basic/02_eta_delayed_execution.py` → `/examples/basic/02_eta_delayed_execution.py`
- `docs/tutorials/concurrency.md`: Update `../../examples/basic/03_bounded_concurrency.py` → `/examples/basic/03_bounded_concurrency.py`
- `docs/tutorials/failures.md`: Update `../../examples/basic/04_failures_and_tracebacks.py` → `/examples/basic/04_failures_and_tracebacks.py`

### 4. Fix External Directory Reference (docs/tutorials/index.md)
- Update `examples/README.md` → `/examples/README.md` to reference project root

### 5. Configure Examples Directory (mkdocs.yml)
- Add `examples/` directory to watch configuration for live reload
- Use absolute paths (`/examples/`) for cross-directory references from docs to project root

## Impact

### Affected Specs
- `documentation-system` - Fix documentation infrastructure warnings and improve navigation

### Affected Files
- `mkdocs.yml` - Navigation configuration and watch settings
- `docs/how-to/workers.md` - Fix 8 broken API links
- `docs/tutorials/quickstart.md` - Fix example link
- `docs/tutorials/delayed-execution.md` - Fix example link
- `docs/tutorials/concurrency.md` - Fix example link
- `docs/tutorials/failures.md` - Fix example link
- `docs/tutorials/index.md` - Fix examples/README.md link
- 19 orphaned docs will be added to nav (no content changes)

### Breaking Changes
- None (documentation-only changes)

### Benefits
- Zero documentation build warnings and info messages
- Complete navigation coverage for all documentation files
- Working API links throughout documentation
- Functional example links
- Improved user experience and documentation discoverability
