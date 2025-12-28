# Installation

## Requirements

- Python 3.8 or higher
- Operating system: Windows, macOS, or Linux

## Install from PyPI

```bash
pip install sitq
```

## Install from Source

```bash
git clone https://github.com/username/sitq.git
cd sitq
pip install -e .
```

## Development Installation

For development with all optional dependencies:

```bash
git clone https://github.com/username/sitq.git
cd sitq
pip install -e ".[dev]"
```

## Verify Installation

```python
import sitq
print(f"sitq version: {sitq.__version__}")
```

## Optional Dependencies

Depending on your use case, you may want to install additional packages:

```bash
# For SQLite backend (default)
pip install sitq

# For enhanced performance
pip install sitq[performance]

# For development tools
pip install sitq[dev]

# Install everything
pip install sitq[all]
```

## Docker Installation

```bash
docker pull sitq/sitq:latest
```

## Next Steps

- [Quickstart Guide](quickstart.md) - Get up and running in 5 minutes
- [Basic Concepts](basic-concepts.md) - Understand the core architecture
- [User Guide](../user-guide/) - Explore all features