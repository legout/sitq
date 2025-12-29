# Test Suite

This directory contains all tests for the sitq project, organized by type.

## Directory Structure

- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests that test multiple components together
- `tests/performance/` - Performance benchmarks
- `tests/validation/` - Tests for validation and documentation

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Unit Tests Only
```bash
pytest tests/unit/
```

### Run Integration Tests Only
```bash
pytest tests/integration/
```

### Run Performance Tests
Performance tests are excluded by default. To run them:
```bash
pytest -m performance
```

### Run Validation Tests
```bash
pytest tests/validation/
```

## Test Organization

### Unit Tests
- Individual component testing
- Fast, isolated tests
- Mock external dependencies when appropriate
- Examples:
  - `test_worker_simple.py` - Basic worker functionality
  - `test_sqlite_backend.py` - SQLite backend operations
  - `test_serialization.py` - Serialization/deserialization

### Integration Tests
- Cross-component testing
- Tests real interactions between components
- Use actual backends (no mocks)
- Examples:
  - `test_queue_worker_integration.py` - Queue + Worker interaction
  - `test_sync_integration.py` - Sync wrapper end-to-end
  - `test_sqlite_memory_db.py` - In-memory SQLite integration

### Performance Tests
- Benchmark performance characteristics
- Not run by default
- Marked with `@pytest.mark.performance`
- Examples:
  - `test_performance_benchmark.py` - Comprehensive benchmarks
  - `test_simple_benchmark.py` - Quick performance check

### Validation Tests
- Documentation and validation testing
- Ensure code quality and API consistency
- Examples:
  - `test_documentation.py` - Validate examples in docs
  - `test_mkdocstrings.py` - Validate docstrings

## Test Configuration

The test suite is configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
addopts = "-v --tb=short"
markers = [
    "performance: marks tests as performance/benchmark tests (deselect with 'not performance')",
]
```

## Import Behavior

Tests import `sitq` directly using `pythonpath = ["."]`, which means:
- Tests import from `src/sitq` (not installed package)
- No bytecode artifacts from previous builds
- Tests always use current source code

## Running Tests with Verbose Output

```bash
pytest -vv  # Extra verbose output
pytest -s    # Show print statements (not recommended)
```

## Coverage

To run tests with coverage reporting:

```bash
pytest --cov=sitq --cov-report=html
```

Coverage report will be generated in `htmlcov/`.
