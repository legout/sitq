# Contributing to sitq

Thank you for your interest in contributing to sitq! This guide will help you get started with contributing to the project.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic knowledge of Python and task queue systems

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/sitq.git
   cd sitq
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify Installation**
   ```bash
   python -m pytest
   python -c "import sitq; print(sitq.__version__)"
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Run Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=sitq --cov-report=html

# Run specific test file
python -m pytest tests/test_queue.py

# Run with verbose output
python -m pytest -v
```

### 4. Code Quality Checks

```bash
# Run linting
python -m flake8 src/sitq

# Run type checking
python -m mypy src/sitq

# Run formatting check
python -m black --check src/sitq

# Run import sorting check
python -m isort --check-only src/sitq
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with a clear description of your changes.

## Code Style Guide

### Python Style

We follow PEP 8 with some additional conventions:

```python
# Good
import sitq
from typing import Dict, List, Optional


class TaskProcessor:
    """Process tasks with proper documentation."""
    
    def __init__(self, queue: sitq.TaskQueue) -> None:
        """Initialize processor.
        
        Args:
            queue: Task queue for processing tasks.
        """
        self.queue = queue
    
    def process_task(self, task_id: str) -> Optional[sitq.Result]:
        """Process a single task.
        
        Args:
            task_id: ID of task to process.
            
        Returns:
            Task result or None if not found.
        """
        try:
            return self.queue.get_result(task_id)
        except sitq.TaskNotFoundError:
            return None
```

### Documentation Style

Use Google-style docstrings:

```python
def enqueue_task(
    self, 
    task: sitq.Task, 
    priority: int = 0,
    max_retries: int = 3
) -> str:
    """Enqueue a task for processing.
    
    Args:
        task: Task to enqueue.
        priority: Task priority (lower numbers = higher priority).
        max_retries: Maximum number of retry attempts.
        
    Returns:
        Task ID for tracking.
        
    Raises:
        QueueFullError: If queue is at capacity.
        SerializationError: If task cannot be serialized.
        
    Example:
        >>> task = sitq.Task(function=my_func, args=[1, 2])
        >>> task_id = queue.enqueue_task(task, priority=1)
        >>> print(f"Task {task_id} enqueued")
    """
```

### Type Hints

Use type hints for all public APIs:

```python
from typing import Dict, List, Optional, Union, Callable, Any

def process_batch(
    self, 
    tasks: List[sitq.Task],
    callback: Optional[Callable[[str, sitq.Result], None]] = None
) -> Dict[str, sitq.Result]:
    """Process a batch of tasks."""
    pass
```

## Testing Guidelines

### Test Structure

```python
# tests/test_queue.py
import pytest
import sitq
from sitq.exceptions import QueueFullError, TaskNotFoundError


class TestTaskQueue:
    """Test suite for TaskQueue."""
    
    @pytest.fixture
    def queue(self):
        """Create a test queue."""
        return sitq.TaskQueue(backend=sitq.SQLiteBackend(":memory:"))
    
    def test_enqueue_task(self, queue):
        """Test task enqueuing."""
        task = sitq.Task(function=lambda x: x * 2, args=[5])
        task_id = queue.enqueue(task)
        
        assert task_id is not None
        assert isinstance(task_id, str)
    
    def test_get_nonexistent_task(self, queue):
        """Test getting non-existent task."""
        with pytest.raises(TaskNotFoundError):
            queue.get_task("nonexistent")
    
    @pytest.mark.parametrize("priority,expected_order", [
        (1, "first"),
        (10, "last"),
        (0, "first"),
    ])
    def test_task_priority(self, queue, priority, expected_order):
        """Test task priority ordering."""
        # Test implementation
        pass
```

### Test Categories

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **Performance Tests**: Test performance characteristics
4. **Error Tests**: Test error conditions and edge cases

### Running Tests

```bash
# Unit tests only
python -m pytest tests/unit/

# Integration tests only
python -m pytest tests/integration/

# Performance tests
python -m pytest tests/performance/ -v

# All tests with coverage
python -m pytest --cov=sitq --cov-report=term-missing
```

## Project Structure

```
sitq/
├── src/
│   └── sitq/
│       ├── __init__.py          # Public API
│       ├── core.py              # Core classes
│       ├── queue.py             # Task queue implementation
│       ├── worker.py            # Worker implementation
│       ├── backends/            # Backend implementations
│       │   ├── __init__.py
│       │   ├── base.py          # Base backend class
│       │   └── sqlite.py        # SQLite backend
│       ├── serialization.py     # Serialization logic
│       ├── exceptions.py        # Exception definitions
│       └── validation.py        # Input validation
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/             # Integration tests
│   ├── performance/             # Performance tests
│   └── conftest.py            # Test configuration
├── docs/                       # Documentation
├── examples/                   # Example code
├── scripts/                    # Development scripts
├── pyproject.toml             # Project configuration
├── README.md                  # Project README
└── CHANGELOG.md               # Version history
```

## Contribution Types

### Bug Fixes

1. Create issue describing the bug
2. Add test that reproduces the bug
3. Fix the bug
4. Ensure test passes
5. Update documentation if needed

### New Features

1. Create issue for discussion
2. Get approval from maintainers
3. Implement feature with tests
4. Update documentation
5. Add examples if appropriate

### Documentation

1. Fix typos and grammar
2. Improve explanations
3. Add examples
4. Update API documentation

### Performance Improvements

1. Benchmark current performance
2. Implement optimization
3. Show performance improvement
4. Ensure no regression in functionality

## Pull Request Process

### Before Submitting

1. **Run all tests**: Ensure everything passes
2. **Check code quality**: Run linting and formatting
3. **Update documentation**: Include relevant changes
4. **Add tests**: Cover new functionality
5. **Test manually**: Verify changes work as expected

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Breaking change

## Testing
- [ ] All tests pass
- [ ] Added new tests for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Examples added if needed
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and quality checks
2. **Code Review**: Maintainers review code for quality and correctness
3. **Discussion**: Address feedback and make necessary changes
4. **Approval**: Get approval from at least one maintainer
5. **Merge**: Merge into main branch

## Development Tools

### Pre-commit Hooks

Install pre-commit hooks for automatic quality checks:

```bash
pip install pre-commit
pre-commit install
```

### Development Scripts

```bash
# Format code
python -m black src/sitq tests/

# Sort imports
python -m isort src/sitq tests/

# Run linting
python -m flake8 src/sitq tests/

# Type checking
python -m mypy src/sitq

# Run all quality checks
python scripts/check_quality.py
```

### Debugging

```bash
# Run with debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run specific test with debugging
python -m pytest tests/test_queue.py::TestTaskQueue::test_enqueue -v -s
```

## Release Process

### Version Management

We follow Semantic Versioning (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. Update version in `__init__.py`
2. Update `CHANGELOG.md`
3. Run full test suite
4. Create release tag
5. Build and publish to PyPI
6. Update documentation

## Community Guidelines

### Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please:

- Be respectful and considerate
- Use inclusive language
- Focus on constructive feedback
- Help others learn and grow

### Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Documentation**: For usage guidance
- **Examples**: For practical implementation

### Communication Channels

- **GitHub Issues**: Project management and bug tracking
- **Pull Requests**: Code review and discussion
- **Discussions**: General questions and ideas

## Recognition

### Contributors

All contributors are recognized in:
- README.md contributors section
- Release notes
- GitHub contributor statistics

### Types of Contributions

We value all types of contributions:
- Code contributions
- Documentation improvements
- Bug reports and feedback
- Community support
- Design and architecture input

## Resources

### Documentation

- [API Reference](../reference/api/sitq.md)
- [User Guide](../how-to/installation.md)
- [Examples](https://github.com/legout/sitq/tree/main/examples/)

### Tools and Libraries

- [pytest](https://pytest.org/) - Testing framework
- [black](https://black.readthedocs.io/) - Code formatting
- [mypy](https://mypy.readthedocs.io/) - Type checking
- [flake8](https://flake8.pycqa.org/) - Linting

### Learning Resources

- [Python Testing](https://docs.python.org/3/library/unittest.html)
- [Type Hints](https://docs.python.org/3/library/typing.html)
- [Semantic Versioning](https://semver.org/)

## Questions?

If you have questions about contributing:

1. Check existing documentation
2. Search existing issues and discussions
3. Create a new discussion for questions
4. Start with small contributions to learn the process

Thank you for contributing to sitq! Your contributions help make the project better for everyone.

## Next Steps

- [Testing Guide](testing.md) - Learn about testing strategy
- [Performance Guide](performance.md) - Performance optimization
- [API Reference](../reference/api/sitq.md) - Detailed API documentation