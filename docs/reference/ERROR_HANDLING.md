# Error Handling Guidelines

This document provides comprehensive guidelines for error handling in sitq, covering exception hierarchy, best practices, and usage patterns.

## Exception Hierarchy

sitq uses a structured exception hierarchy to provide clear, actionable error information:

```
SitqError (base exception)
├── TaskQueueError (task queue operations)
├── BackendError (backend operations)
├── WorkerError (worker operations)
├── ValidationError (input validation)
├── SerializationError (serialization/deserialization)
├── ConnectionError (connection issues)
├── TaskExecutionError (task execution failures)
├── TimeoutError (operation timeouts)
├── ResourceExhaustionError (resource limits)
└── ConfigurationError (configuration issues)
```

## Core Principles

### 1. Use Domain-Specific Exceptions

Always use sitq's domain-specific exceptions rather than generic Python exceptions:

```python
# Good
raise ValidationError("Task cannot be None - provide a valid Task instance", parameter="task")

# Avoid
raise ValueError("Task cannot be None")
```

### 2. Provide Actionable Error Messages

Error messages should:
- Clearly state what went wrong
- Suggest how to fix the issue
- Include relevant context

```python
# Good
raise ValidationError("Task cannot be None - provide a valid Task instance", parameter="task")

# Poor
raise ValidationError("Invalid task")
```

### 3. Preserve Exception Chains

Always preserve the original exception as the cause:

```python
try:
    # Some operation that might fail
    result = risky_operation()
except Exception as e:
    raise BackendError(
        f"Failed to connect to database: {e}",
        operation="connect",
        backend_type="sqlite",
        cause=e
    ) from e
```

## Input Validation

### Validation Pattern

Use the `validate()` function for consistent input validation:

```python
from sitq.validation import validate

def my_function(task_id: str, timeout: Optional[int] = None):
    # Required parameters
    validate(task_id, "task_id").is_required().is_non_empty_string().validate()
    
    # Optional parameters with null checks
    if timeout is not None:
        validate(timeout, "timeout").is_non_negative_number().validate()
```

### Fluent Validation Interface

The validation builder provides a fluent interface:

```python
validate(value, "parameter_name")
    .is_required()
    .is_string()
    .min_length(3)
    .max_length(100)
    .validate()
```

### Available Validators

- `is_required()` - Value must not be None
- `is_string()` - Value must be a string
- `is_callable()` - Value must be callable
- `is_positive_number()` - Value must be > 0
- `is_non_negative_number()` - Value must be >= 0
- `is_integer()` - Value must be an integer
- `is_timezone_aware()` - Datetime must have timezone
- `min_length(n)` - String/list minimum length
- `max_length(n)` - String/list maximum length
- `in_range(min, max)` - Number within range
- `in_choices(choices)` - Value in allowed choices

## Error Handling Patterns

### 1. Backend Operations

```python
async def enqueue(self, task: Task) -> None:
    # Validate input
    if task is None:
        raise ValidationError("Task cannot be None", parameter="task")
    
    try:
        # Backend operation
        await self._database.insert(task)
    except DatabaseError as e:
        # Wrap in domain-specific exception
        raise BackendError(
            f"Failed to enqueue task {task.id}: {e}",
            operation="enqueue",
            task_id=task.id,
            backend_type="sqlite",
            cause=e
        ) from e
```

### 2. Task Execution

```python
async def _execute_task(self, task: Task) -> Any:
    try:
        # Deserialize task
        envelope = self.serializer.deserialize_task_envelope(task.func)
    except Exception as e:
        raise SerializationError(
            f"Failed to deserialize task {task.id}: {e}",
            operation="deserialize",
            data_type="task_envelope",
            cause=e
        ) from e
    
    try:
        # Execute function
        result = await envelope["func"](*envelope["args"], **envelope["kwargs"])
        return result
    except Exception as e:
        raise TaskExecutionError(
            f"Task {task.id} execution failed: {e}",
            task_id=task.id,
            function_name=envelope["func"].__name__,
            cause=e
        ) from e
```

### 3. Retry Logic

Use the retry decorators for transient failures:

```python
from sitq.validation import retry_async

@retry_async(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    backoff_factor=2.0,
    jitter=True,
    retryable_exceptions=[ConnectionError, TimeoutError]
)
async def connect_to_database(self) -> Connection:
    return await self._create_connection()
```

### 4. Context Managers

Use context managers for proper resource cleanup:

```python
async def process_tasks():
    try:
        async with TaskQueue(backend) as queue:
            task_id = await queue.enqueue(process_data, data)
            result = await queue.get_result(task_id)
            return result
    except TaskQueueError as e:
        logger.error(f"Task queue operation failed: {e}")
        raise
```

## Exception Context

All sitq exceptions support context information:

```python
raise BackendError(
    "Database connection failed",
    operation="connect",
    backend_type="sqlite",
    connection_details="database_path=/tmp/tasks.db",
    cause=original_exception
)
```

Available context fields vary by exception type:
- `task_id` - Task identifier
- `operation` - Operation being performed
- `backend_type` - Backend implementation
- `worker_id` - Worker identifier
- `parameter` - Validation parameter name
- `value` - Validation parameter value
- `connection_details` - Connection information
- `function_name` - Function being executed
- `execution_time` - Task execution duration
- `timeout_seconds` - Timeout value
- `resource_type` - Resource type
- `current_usage` - Current resource usage
- `limit` - Resource limit

## Testing Error Handling

### Testing Exception Types

```python
def test_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        validate(None, "param").is_required().validate()
    
    assert exc_info.value.parameter == "param"
    assert "cannot be None" in str(exc_info.value).lower()
```

### Testing Exception Context

```python
def test_backend_error_context():
    with pytest.raises(BackendError) as exc_info:
        # Trigger backend error
        backend.connect()
    
    error = exc_info.value
    assert error.operation == "connect"
    assert error.backend_type == "sqlite"
    assert error.cause is not None
```

### Testing Retry Logic

```python
@pytest.mark.asyncio
async def test_retry_logic():
    mock_func = AsyncMock(side_effect=[ConnectionError("Failed"), "success"])
    
    @retry_async(max_attempts=2, base_delay=0.01)
    async def test_func():
        return await mock_func()
    
    result = await test_func()
    assert result == "success"
    assert mock_func.call_count == 2
```

## Best Practices

### DO:
- ✅ Use domain-specific exceptions
- ✅ Provide actionable error messages
- ✅ Include relevant context information
- ✅ Preserve exception chains with `from e`
- ✅ Validate all public method inputs
- ✅ Use retry logic for transient failures
- ✅ Handle exceptions at appropriate abstraction levels
- ✅ Log errors with sufficient context

### DON'T:
- ❌ Use generic exceptions (ValueError, RuntimeError) for domain errors
- ❌ Swallow exceptions without proper handling
- ❌ Lose exception context
- ❌ Provide vague error messages
- ❌ Skip input validation
- ❌ Retry non-transient failures
- ❌ Catch Exception too broadly
- ❌ Return error codes instead of raising exceptions

## Error Recovery Strategies

### 1. Validation Errors
- **Strategy**: Fail fast with clear messages
- **Recovery**: Fix input and retry

### 2. Connection Errors
- **Strategy**: Retry with exponential backoff
- **Recovery**: Automatic retry or manual reconnection

### 3. Serialization Errors
- **Strategy**: Fail immediately (non-retryable)
- **Recovery**: Fix object serialization compatibility

### 4. Task Execution Errors
- **Strategy**: Record failure, don't retry automatically
- **Recovery**: Fix task logic and resubmit

### 5. Timeout Errors
- **Strategy**: Increase timeout or optimize operation
- **Recovery**: Retry with longer timeout

### 6. Resource Exhaustion
- **Strategy**: Back off and retry later
- **Recovery**: Scale resources or reduce load

## Logging Integration

sitq exceptions are designed to work well with structured logging:

```python
import logging

logger = logging.getLogger(__name__)

try:
    await queue.enqueue(task)
except TaskQueueError as e:
    logger.error(
        "Task queue operation failed",
        extra={
            "error_type": type(e).__name__,
            "task_id": e.task_id,
            "operation": e.operation,
            "message": str(e),
            "cause": str(e.cause) if e.cause else None
        }
    )
    raise
```

## Migration Guide

### From Generic Exceptions

Replace generic exceptions with sitq equivalents:

```python
# Before
raise ValueError("Invalid timeout value")

# After
raise ValidationError("Timeout must be non-negative - provide a valid timeout value", parameter="timeout")
```

### Adding Context

Enhance existing exceptions with context:

```python
# Before
raise RuntimeError("Database connection failed")

# After
raise ConnectionError(
    "Failed to connect to SQLite database '/tmp/tasks.db': connection refused",
    backend_type="sqlite",
    connection_details="database_path=/tmp/tasks.db",
    cause=original_exception
)
```

This comprehensive error handling system ensures that sitq provides clear, actionable error information while maintaining robust error recovery capabilities.