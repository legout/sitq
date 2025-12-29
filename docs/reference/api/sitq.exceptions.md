# sitq.exceptions

Exception classes for sitq error handling.

```{eval-rst}
.. automodule:: sitq.exceptions
```

## Exception Hierarchy

```
SitqError
├── TaskQueueError
├── BackendError
├── WorkerError
├── ValidationError
├── SerializationError
├── ConnectionError
├── TaskExecutionError
├── TimeoutError
├── ResourceExhaustionError
├── ConfigurationError
└── SyncTaskQueueError
```

## SitqError

```{eval-rst}
.. autoexception:: SitqError
```

Base exception for all sitq errors.

### Example

```python
from sitq import SitqError

try:
    # sitq operations
    pass
except SitqError as e:
    print(f"sitq error: {e}")
```

## TaskQueueError

```{eval-rst}
.. autoexception:: TaskQueueError
```

Exception raised by [`TaskQueue`](sitq.queue.md) for queue-related errors.

## BackendError

```{eval-rst}
.. autoexception:: BackendError
```

Exception raised by [`Backend`](sitq.backends.base.md) implementations.

## WorkerError

```{eval-rst}
.. autoexception:: WorkerError
```

Exception raised by [`Worker`](sitq.worker.md) for worker-related errors.

## ValidationError

```{eval-rst}
.. autoexception:: ValidationError
```

Exception raised during input validation.

### Example

```python
from sitq import ValidationError

try:
    backend = SQLiteBackend(None)  # Invalid: None
except ValidationError as e:
    print(f"Validation error: {e}")
```

## SerializationError

```{eval-rst}
.. autoexception:: SerializationError
```

Exception raised during serialization or deserialization.

### Example

```python
from sitq import SerializationError

try:
    data = serializer.dumps(non_serializable_obj)
except SerializationError as e:
    print(f"Serialization failed: {e}")
```

## ConnectionError

```{eval-rst}
.. autoexception:: ConnectionError
```

Exception raised for connection-related errors.

## TaskExecutionError

```{eval-rst}
.. autoexception:: TaskExecutionError
```

Exception raised during task execution.

## TimeoutError

```{eval-rst}
.. autoexception:: TimeoutError
```

Exception raised when operations timeout.

### Example

```python
from sitq import TimeoutError

try:
    result = await queue.get_result(task_id, timeout=5)
except TimeoutError as e:
    print(f"Task timed out: {e}")
```

## ResourceExhaustionError

```{eval-rst}
.. autoexception:: ResourceExhaustionError
```

Exception raised when system resources are exhausted.

## ConfigurationError

```{eval-rst}
.. autoexception:: ConfigurationError
```

Exception raised for configuration-related errors.

## SyncTaskQueueError

```{eval-rst}
.. autoexception:: SyncTaskQueueError
```

Exception raised by [`SyncTaskQueue`](sitq.sync.md) for sync-specific errors.

## Error Handling Best Practices

### Always Check Status

```python
result = await queue.get_result(task_id)

if result:
    if result.status == "success":
        value = queue.deserialize_result(result)
    elif result.status == "failed":
        print(f"Task failed: {result.error}")
```

### Catch Specific Exceptions

```python
from sitq import (
    ValidationError,
    SerializationError,
    BackendError,
    WorkerError
)

try:
    task_id = await queue.enqueue(func, args)
except ValidationError as e:
    print(f"Invalid input: {e}")
except SerializationError as e:
    print(f"Serialization failed: {e}")
except BackendError as e:
    print(f"Backend error: {e}")
```

### Use Finally for Cleanup

```python
worker_task = None
try:
    worker_task = asyncio.create_task(worker.start())
    await asyncio.sleep(10)
finally:
    if worker_task:
        await worker.stop()
```

## See Also

- [Error Handling Guide](../../reference/ERROR_HANDLING.md) - Comprehensive error handling
- [Handling Failures](../../how-to/handle-failures.md) - Practical error handling
- [Troubleshooting](../../how-to/troubleshooting.md) - Common issues and solutions
