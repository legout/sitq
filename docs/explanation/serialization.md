# Serialization

Understanding how sitq serializes and deserializes tasks and results.

## Overview

Serialization is the process of converting Python objects into bytes for storage and transmission. sitq uses **cloudpickle** by default to handle complex Python objects including lambdas, closures, and class instances.

## Default Serialization: Cloudpickle

### What Cloudpickle Handles

Cloudpickle is more powerful than standard pickle:

```python
from sitq import CloudpickleSerializer

serializer = CloudpickleSerializer()

# Can serialize:
# - Functions with closures
def make_adder(n):
    def adder(x):
        return x + n
    return adder

data = serializer.dumps(make_adder)
func = serializer.loads(data)

# - Lambda functions
lambda_func = lambda x: x * 2
data = serializer.dumps(lambda_func)
func = serializer.loads(data)

# - Class instances
class MyClass:
    def __init__(self, value):
        self.value = value

instance = MyClass(42)
data = serializer.dumps(instance)
obj = serializer.loads(data)

# - Async functions
async def async_func(x):
    return x * 2

data = serializer.dumps(async_func)
func = serializer.loads(data)
```

### Why Cloudpickle?

Standard pickle has limitations:
- Can't serialize lambdas
- Can't serialize functions with closures
- Can't serialize certain class types
- Limited module-level function support

Cloudpickle solves these by:
- Capturing closure variables
- Serializing function code
- Handling dynamic module imports

## Serialization Process

### Task Serialization

When enqueuing a task:

```python
from sitq import TaskQueue, SQLiteBackend

backend = SQLiteBackend("tasks.db")
queue = TaskQueue(backend=backend)

# Enqueue task (automatically serialized)
task_id = await queue.enqueue(
    my_function,    # Function to serialize
    "arg1", "arg2"  # Arguments to serialize
    kwarg="value"    # Keyword arguments to serialize
)
```

Internally:
1. Capture function object
2. Capture arguments
3. Serialize using CloudpickleSerializer
4. Store bytes in database

### Result Deserialization

When retrieving a result:

```python
# Get serialized result
result = await queue.get_result(task_id)

# Check status
if result and result.status == "success":
    # Deserialize to get Python object
    value = queue.deserialize_result(result)
    print(f"Result: {value}")
```

## Serialization Constraints

### Serializable Types

**Works with cloudpickle:**
- Primitive types (int, float, str, bool, None)
- Collections (list, tuple, dict, set)
- Functions (including lambdas)
- Class instances
- Async functions
- Custom objects with `__dict__`
- Most standard library types

**Challenging to serialize:**
- File handles, sockets, database connections
- Thread locks, semaphores
- Running asyncio tasks
- C extensions
- Open files

### Best Practices for Task Functions

**Do:**
```python
# Use serializable arguments
async def process_data(data: dict) -> dict:
    """Function with serializable arguments."""
    return {"result": data["value"] * 2}

# Use basic types
async def calculate(x: int, y: int) -> int:
    """Function with basic types."""
    return x + y
```

**Don't:**
```python
# Don't pass non-serializable objects
async def process_file(file_handle):
    """BAD: File handle can't be serialized."""
    content = file_handle.read()
    return process_content(content)

# Do: Pass file path instead
async def process_file(filepath: str):
    """GOOD: String can be serialized."""
    with open(filepath, "r") as f:
        content = f.read()
    return process_content(content)
```

### Large Objects

For large objects, consider:

```python
# 1. Use references instead of values
async def process_by_id(task_id: int):
    """Process by ID rather than passing large object."""
    data = database.query(task_id)
    return process_data(data)

# 2. Split into multiple tasks
async def process_large_data(data: list):
    """Split large data into chunks."""
    chunk_size = 100
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        await queue.enqueue(process_chunk, chunk)
```

## Custom Serialization

### Implementing Custom Serializer

Create custom serializer by implementing [`Serializer`](../reference/api/sitq.serialization.md) interface:

```python
from sitq.serialization import Serializer

class MySerializer(Serializer):
    """Custom serializer."""
    
    def dumps(self, obj) -> bytes:
        """Serialize object to bytes."""
        # Your serialization logic
        return my_serialize(obj)
    
    def loads(self, data: bytes):
        """Deserialize bytes to object."""
        # Your deserialization logic
        return my_deserialize(data)

# Use with queue or worker
from sitq import TaskQueue, Worker, SQLiteBackend

serializer = MySerializer()
backend = SQLiteBackend("tasks.db")
queue = TaskQueue(backend=backend, serializer=serializer)
worker = Worker(backend, serializer=serializer)
```

### JSON Serialization Example

```python
import json
from sitq.serialization import Serializer

class JsonSerializer(Serializer):
    """JSON serializer for simple types."""
    
    def dumps(self, obj) -> bytes:
        return json.dumps(obj).encode('utf-8')
    
    def loads(self, data: bytes):
        return json.loads(data.decode('utf-8'))

# Use with queue
serializer = JsonSerializer()
queue = TaskQueue(backend=backend, serializer=serializer)
```

### MessagePack Serialization Example

```python
import msgpack
from sitq.serialization import Serializer

class MsgpackSerializer(Serializer):
    """MessagePack serializer for efficiency."""
    
    def dumps(self, obj) -> bytes:
        return msgpack.packb(obj)
    
    def loads(self, data: bytes):
        return msgpack.unpackb(data)

serializer = MsgpackSerializer()
```

### Encrypted Serialization

```python
from cryptography.fernet import Fernet
from sitq.serialization import Serializer

class EncryptedSerializer(Serializer):
    """Serializer with encryption."""
    
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def dumps(self, obj) -> bytes:
        data = pickle.dumps(obj)
        return self.cipher.encrypt(data)
    
    def loads(self, data: bytes):
        decrypted = self.cipher.decrypt(data)
        return pickle.loads(decrypted)

# Use encryption
key = Fernet.generate_key()
serializer = EncryptedSerializer(key)
queue = TaskQueue(backend=backend, serializer=serializer)
```

## Serialization Performance

### Measuring Serialization Time

```python
import time
from sitq import CloudpickleSerializer

serializer = CloudpickleSerializer()

# Measure serialization
data = {"large": "data" * 10000}
start = time.time()
serialized = serializer.dumps(data)
serialize_time = time.time() - start

size_bytes = len(serialized)
size_mb = size_bytes / (1024 * 1024)

print(f"Serialization: {serialize_time:.3f}s")
print(f"Size: {size_mb:.2f} MB")
```

### Optimization Strategies

1. **Reduce object size**
   ```python
   # Bad: Large object
   large_obj = {"data": [i for i in range(100000)]}
   
   # Good: Split into smaller tasks
   for chunk in split_data(large_obj):
       await queue.enqueue(process_chunk, chunk)
   ```

2. **Use efficient serialization**
   ```python
   # Cloudpickle is flexible but not always fastest
   # For simple types, JSON or MessagePack may be faster
   serializer = JsonSerializer()  # For simple dicts/lists
   ```

3. **Avoid redundant data**
   ```python
   # Bad: Duplicate data
   task_data = {"value": 42, "metadata": {"value": 42}}
   
   # Good: Single source of truth
   task_data = {"value": 42, "metadata": {"ref": "data-42"}}
   ```

## Common Issues

### Serialization Errors

**Symptoms:**
- Error during task enqueue
- Task fails to start
- Result can't be deserialized

**Debugging:**
```python
try:
    task_id = await queue.enqueue(my_function, args)
except SerializationError as e:
    print(f"Serialization failed: {e}")
    # Check object types
    print(f"Function: {my_function}")
    print(f"Args: {args}")
```

### Memory Growth

**Symptoms:**
- Memory increases over time
- Out of memory errors
- Performance degrades

**Solutions:**
```python
# Clear old results
async def cleanup_old_results(queue, age_hours=24):
    """Remove results older than age."""
    # Implementation depends on backend capabilities
    pass

# Use generators instead of lists
async def task_generator():
    for i in range(1000):
        yield lambda x=i: x * 2

for task_func in task_generator():
    await queue.enqueue(task_func)
```

## Best Practices

1. **Use cloudpickle** for complex Python objects
2. **Pass serializable types** to task functions
3. **Avoid closures** when possible (simpler serialization)
4. **Use references** instead of large objects
5. **Consider custom serializers** for specific use cases (JSON, MessagePack)
6. **Test serialization** before production use
7. **Monitor serialization time** for performance optimization

## What's Next?

- [Architecture](architecture.md) - System architecture overview
- [Limitations](limitations.md) - Known constraints
- [API Reference](../reference/api/sitq.serialization.md) - Serializer interface

## See Also

- [`Serializer`](../reference/api/sitq.serialization.md) - Serializer base class
- [`CloudpickleSerializer`](../reference/api/sitq.serialization.md) - Default implementation
- [Error Handling](../reference/ERROR_HANDLING.md) - SerializationError
