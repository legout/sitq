# Change: Improve docstring coverage for v1.0 public APIs

## Why

The sitq project has 91.7% public API docstring coverage but significant gaps remain in critical modules (`backends/sqlite.py`, `exceptions.py`, `serialization.py`). These gaps will produce poor or incomplete API reference documentation via mkdocstrings, reducing the quality and usability of the automatically generated API reference.

## What Changes

- Add complete Google-style docstrings to all public APIs lacking documentation
- Expand minimal docstrings to include Args, Returns, and Raises sections
- Ensure all exception `__init__` methods document their parameters
- Provide consistent documentation style across all modules

## Impact

- Affected specs:
  - `documentation-system` (improve API reference quality)
- Affected files:
  - `src/sitq/backends/sqlite.py` (10 of 13 core methods need docs)
  - `src/sitq/exceptions.py` (12 exception `__init__` methods need parameter docs)
  - `src/sitq/serialization.py` (3 methods need Args/Returns)
  - `src/sitq/backends/base.py` (abstract methods need Args/Returns/Raises)
- **BREAKING**: None (documentation-only)
