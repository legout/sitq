# Installation

## Requirements

- Python 3.13 or higher
- Operating system: Windows, macOS, or Linux

## Install from PyPI

```bash
pip install sitq
```

## Install from Source

```bash
git clone https://github.com/legout/sitq.git
cd sitq
pip install -e .
```

## Development Installation

For development with all optional dependencies:

```bash
git clone https://github.com/legout/sitq.git
cd sitq
pip install -e ".[dev]"
```

## Supported Install Methods

### Standard Installation

The standard installation includes all core dependencies:

- `sqlalchemy>=2.0` - Database abstraction layer
- `aiosqlite>=0.19` - Async SQLite support
- `cloudpickle>=3.0` - Task and result serialization
- `loguru>=0.7` - Logging

```bash
pip install sitq
```

### Development Installation

Development installation includes testing and development tools:

```bash
pip install -e ".[dev]"
```

Development dependencies include:
- `pytest>=9.0.1` - Testing framework
- `pytest-asyncio>=1.3.0` - Async testing support
- `ruff>=0.12.8` - Linting and formatting
- `ipython>=9.4.0` - Enhanced Python REPL
- `marimo>=0.14.16` - Notebook support

## Verify Installation

```python
import sitq
print(f"sitq version: {sitq.__version__}")
```

## Backend-Specific Dependencies

The SQLite backend is included in the standard installation. No additional dependencies are required for the current implementation.

## Next Steps

- [Quickstart Guide](../tutorials/quickstart.md) - Get up and running in 5 minutes
- [API Reference](../reference/api/) - Complete API documentation
- [How-to Guides](../how-to/) - Explore all features