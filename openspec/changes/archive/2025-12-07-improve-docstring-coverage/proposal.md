# Change: Improve Docstring Coverage for API Documentation

## Why
The sitq codebase has solid engineering but inconsistent docstring coverage that prevents generation of high-quality API documentation with mkdocstrings. Critical gaps include empty `__init__.py`, missing method docstrings, and inconsistent formatting.

## What Changes
- Add comprehensive docstrings to all public APIs
- Create proper `__init__.py` with public API exports
- Standardize docstring format to Google-style consistently
- Add `__all__` lists to define public API boundaries
- Enhance dataclass documentation with field descriptions
- Add usage examples to major classes

## Impact
- Affected specs: task-queue-core, worker-core, backend-sqlite, serialization-core, sync-task-queue
- Affected code: All public APIs in `src/sitq/`
- **BREAKING**: None (documentation-only change)
- Enables: High-quality mkdocstrings API documentation generation