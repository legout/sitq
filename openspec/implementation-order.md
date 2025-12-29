# Implementation Order for OpenSpec Changes (v1 Refactor)

This document defines the recommended implementation order for the **active** OpenSpec changes under `openspec/changes/` and highlights what can be done in parallel.

## Active Changes

### Documentation Quality
1. `improve-docstring-coverage` (26 tasks)

### Documentation Refactor (Diataxis)
1. `refactor-docs-diataxis-ia`
2. `revise-docs-portal-tutorials-howto-explanation-reference`
3. `remove-obsolete-docs`
4. `update-docs-validation-tests`

### v1 Core Refactor (Archived)
*The following changes are archived as completed in `openspec/changes/archive/`*:
1. `2025-12-14-stabilize-v1-core`
2. `2025-12-14-fix-worker-concurrency`
3. `2025-12-14-test-suite-organization`
4. `2025-12-14-align-docs-and-deps-v1`

## Recommended Order

### Documentation Quality Order

#### 1) `improve-docstring-coverage` (foundation)
**Why first**
- Should be done before API reference pages are finalized
- Directly impacts mkdocstrings API reference quality
- Provides complete docstring coverage before documentation refactor

**Primary outputs**
- Complete docstrings for all public APIs in `backends/sqlite.py`, `exceptions.py`, `serialization.py`
- Expanded docstrings for `Backend` abstract methods
- 100% public API coverage with Google-style formatting

### Documentation Refactor Order

#### 1) `refactor-docs-diataxis-ia` (foundation)
**Why first**
- Establishes the new Diataxis directory structure (`tutorials/`, `how-to/`, `reference/`, `explanation/`)
- Fixes MkDocs navigation to prevent missing file errors
- Enables all subsequent documentation work to have a clear home

**Primary outputs**
- Diataxis directory layout under `docs/`
- Updated `docs/mkdocs.yml` with correct `nav:` and repo metadata
- Removal of `git-committers` plugin

#### 2) `revise-docs-portal-tutorials-howto-explanation-reference` (content)
**Why second**
- Depends on the structure from step 1
- Provides the actual content for the new IA (portal, tutorials, how-to, explanation, reference)
- Aligns installation docs with `pyproject.toml` (Python >= 3.13)

**Primary outputs**
- Rewritten `docs/index.md` as a Diataxis portal
- Accurate `docs/installation.md`
- Tutorials including rewritten `docs/tutorials/interactive-tutorial.ipynb`
- How-to guides, explanation pages, and mkdocstrings API reference stubs

#### 3) `remove-obsolete-docs` (cleanup)
**Why third**
- Must wait until replacements from step 2 exist
- Removes legacy content that references unimplemented APIs
- Cleans up nav to prevent dead links

**Primary outputs**
- Deleted `docs/user-guide/` pages and other obsolete content
- Clean `docs/mkdocs.yml` nav with no broken links
- Documentation with no "future work" or speculative sections

#### 4) `update-docs-validation-tests` (validation)
**Why last**
- Tests should validate the final Diataxis structure
- Ensures notebook location and snippet syntax checking align with new docs
- Safe to update after all other docs work is stable

**Primary outputs**
- Updated `tests/validation/test_documentation.py` for Diataxis layout
- Retained/enhanced code block syntax validation
- Assertions for `docs/tutorials/interactive-tutorial.ipynb` existence

### v1 Core Refactor Order (Archived)

#### 1) `2025-12-14-stabilize-v1-core` (foundation)
**Why first**
- Unblocks everything else by restoring importability and clarifying core semantics (notably `TaskQueue.get_result(..., timeout)` returns `None`).
- Fixes baseline issues in `TaskQueue`, `SyncTaskQueue`, serializer, validation, and SQLite connection/transaction handling that can otherwise derail any follow-on work.

**Primary outputs**
- Clean imports from source (no reliance on committed bytecode artifacts).
- Stable, spec-aligned behavior for timeout and sync wrapper error handling.

### 2) `2025-12-14-fix-worker-concurrency` (correctness + performance)
**Why second**
- Depends on a stable core import surface and baseline backend behavior.
- Establishes correct bounded concurrency and reliable shutdown semantics, which improves both real usage and test determinism.

**Primary outputs**
- Semaphore/dispatch logic that enforces `max_concurrency`.
- Reliable task tracking so `stop()` waits for in-flight work.

### 3) `2025-12-14-test-suite-organization` (reduce friction)
**Why third**
- Moving/renaming tests tends to create merge conflicts; doing it after the main functional fixes reduces churn.
- Once core behavior stabilizes, you can reorganize tests without repeatedly revisiting paths/import conventions.

**Primary outputs**
- `tests/` layout (unit/integration vs performance).
- Benchmarks opt-in (default `pytest` stays fast).

### 4) `2025-12-14-align-docs-and-deps-v1` (user-facing alignment)
**Why last**
- Docs and examples should reflect the final stabilized API semantics and worker behavior.
- Dependency trimming is safer once you’ve confirmed what v1 runtime code actually imports/needs.

**Primary outputs**
- README/MkDocs aligned to v1 scope.
- Runnable `examples/` “first success” script.
- Reduced default dependencies; deferred backends moved to optional installs (if desired).

## Parallelization Guidance

### Documentation Quality vs Refactor Parallelization
**Recommended parallel tracks**:
- Track A: Implement `improve-docstring-coverage` (code-only changes)
- Track B: Implement `refactor-docs-diataxis-ia` + `revise-docs-portal-...` (docs structure and content)

Rationale: Docstring changes only touch `src/sitq/**/*.py`, while docs refactor touches `docs/**` and `docs/mkdocs.yml`. These can proceed independently until the final API reference integration step.

### Documentation Refactor Parallelization
**Sequential is recommended** due to tight dependencies:
- `refactor-docs-diataxis-ia` (1) must be complete before content can be added
- `revise-docs-portal-tutorials-howto-explanation-reference` (2) must be complete before obsolete docs can be removed
- `remove-obsolete-docs` (3) and `update-docs-validation-tests` (4) could be done in parallel after step 2, but this is low value

### v1 Core Refactor Parallelization (Archived)

You *could* implement some of these in parallel, but expect merge conflicts if two efforts touch the same files.

### Safe(ish) parallel tracks (recommended)
- After (1) is merged:
   - Track A: implement (2) `fix-worker-concurrency`
   - Track B: implement (4) `align-docs-and-deps-v1` **only for docs** (README/docs edits)

Rationale: worker concurrency changes mostly touch `src/sitq/worker.py`, while docs work mostly touches `README.md` and `docs/**`.

### Parallel tracks with higher conflict risk
- (3) `test-suite-organization` in parallel with (1) or (2):
   - likely conflicts because both phases typically modify tests, imports, and CI/pytest configuration.

If you want to parallelize this anyway, do it on a separate branch and merge it only once (1) and (2) are stable, then resolve conflicts once.

## Validation Checkpoints (recommended)

### Documentation Quality Checkpoints
After `improve-docstring-coverage` is implemented:
- Run `openspec validate improve-docstring-coverage --strict`
- Run `mkdocs build` and verify all API reference pages render with complete docs
- Spot-check critical pages: `sitq.backends.sqlite`, `sitq.exceptions`, `sitq.serialization`

### Documentation Refactor Checkpoints
After each documentation change-id is implemented:
- Run `openspec validate <change-id> --strict`
- Run `mkdocs build` to ensure navigation and links work
- For steps 2-4, spot-check that portal/tutorial/how-to/explanation/reference sections are present and link correctly
- After step 3, verify no "future work" or speculative content remains
- After step 4, run `pytest tests/validation/` to confirm updated tests pass

### v1 Core Refactor Checkpoints (Archived)
After each change-id is implemented:
- Run `openspec validate <change-id> --strict`
- Run the default pytest suite (fast path; exclude performance tests by default)
- Run one end-to-end example (enqueue → worker → get_result) to confirm the user workflow
