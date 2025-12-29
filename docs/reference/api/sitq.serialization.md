# sitq.serialization

Serialization interface and implementations.

```{eval-rst}
.. automodule:: sitq.serialization
```

## Serializer

```{eval-rst}
.. autoclass:: Serializer
```

Abstract base class for implementing custom serializers.

### Abstract Methods

#### `dumps(obj) -> bytes`

Serialize object to bytes.

**Parameters:**
- `obj` (Any): Object to serialize

**Returns:**
- `bytes`: Serialized object

**Raises:**
- [`SerializationError`](sitq.exceptions.md): If object cannot be serialized

#### `loads(data: bytes) -> Any`

Deserialize bytes to object.

**Parameters:**
- `data` (bytes): Serialized data

**Returns:**
- `Any`: Deserialized object

**Raises:**
- [`SerializationError`](sitq.exceptions.md): If data cannot be deserialized

## CloudpickleSerializer

```{eval-rst}
.. autoclass:: CloudpickleSerializer
```

Default serializer implementation using cloudpickle.

### Methods

#### `dumps(obj) -> bytes`

Serialize object using cloudpickle.

**Example:**
```python
from sitq import CloudpickleSerializer

serializer = CloudpickleSerializer()
data = serializer.dumps({"key": "value"})
```

#### `loads(data: bytes) -> Any`

Deserialize bytes using cloudpickle.

**Example:**
```python
obj = serializer.loads(data)
print(obj)  # {"key": "value"}
```

## Usage Example

```python
from sitq import TaskQueue, SQLiteBackend, CloudpickleSerializer
import asyncio

# Create custom serializer
serializer = CloudpickleSerializer()

# Use with queue
backend = SQLiteBackend("tasks.db")
queue = TaskQueue(backend=backend, serializer=serializer)

# Enqueue task
task_id = await queue.enqueue(my_function, "arg")

# Get result
result = await queue.get_result(task_id)
if result and result.status == "success":
    value = queue.deserialize_result(result)
    print(f"Result: {value}")
```

## Implementing Custom Serializer

```python
from sitq.serialization import Serializer
import json

class JsonSerializer(Serializer):
    """JSON serializer for simple types."""
    
    def dumps(self, obj) -> bytes:
        """Serialize to JSON."""
        return json.dumps(obj).encode('utf-8')
    
    def loads(self, data: bytes) -> Any:
        """Deserialize from JSON."""
        return json.loads(data.decode('utf-8'))

# Use custom serializer
serializer = JsonSerializer()
queue = TaskQueue(backend=backend, serializer=serializer)
```

## Serialization Considerations

### What Can Be Serialized

**Works with cloudpickle:**
- Python primitives (int, float, str, bool, None)
- Collections (list, tuple, dict, set)
- Functions and lambdas (with closures)
- Class instances
- Async functions
- Most standard library types

### What Cannot Be Serialized

**Problematic to serialize:**
- File handles, sockets, database connections
- Thread locks, semaphores, events
- Running asyncio tasks and event loops
- C extension objects
- Open file objects

**Solutions:**
- Pass file paths instead of file handles
- Close connections before enqueuing
- Use serializable wrappers

## See Also

- [`Serializer`](sitq.serialization.md) - Serializer base class
- [Serialization Guide](../../explanation/serialization.md) - Serialization details and best practices
- [`SerializationError`](sitq.exceptions.md) - Serialization exceptions
