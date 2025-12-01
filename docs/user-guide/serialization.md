# Serialization

Serialization is the process of converting tasks and results to/from a format that can be stored and transmitted. sitq handles serialization automatically, but understanding how it works is important for advanced use cases.

## Default Serialization

sitq uses cloudpickle by default for maximum compatibility:

```python
import sitq

# Default serialization (cloudpickle)
queue = sitq.TaskQueue(backend=sitq.SQLiteBackend())

def complex_function(data, callback=None):
    """Function with complex objects."""
    result = process_data(data)
    if callback:
        callback(result)
    return result

# Complex objects are serialized automatically
task = sitq.Task(
    function=complex_function,
    args=[{"complex": "data"}],
    kwargs={"callback": lambda x: print(f"Processed: {x}")}
)

task_id = queue.enqueue(task)  # Automatically serialized
```

## Serialization Configuration

### Using Different Serializers

```python
import pickle
import json

# Use standard pickle
queue = sitq.TaskQueue(
    backend=sitq.SQLiteBackend(),
    serializer=pickle
)

# Use JSON for simple data types
def simple_task(data):
    """Simple task with JSON-serializable data."""
    return {"result": data * 2}

queue = sitq.TaskQueue(
    backend=sitq.SQLiteBackend(),
    serializer=json
)
```

### Custom Serialization

```python
import yaml
import base64

class YAMLSerializer:
    """Custom YAML serializer."""
    
    def dumps(self, obj):
        """Serialize object to YAML string."""
        yaml_str = yaml.dump(obj)
        return base64.b64encode(yaml_str.encode()).decode()
    
    def loads(self, data):
        """Deserialize YAML string to object."""
        yaml_str = base64.b64decode(data.encode()).decode()
        return yaml.safe_load(yaml_str)

# Use custom serializer
queue = sitq.TaskQueue(
    backend=sitq.SQLiteBackend(),
    serializer=YAMLSerializer()
)
```

## Serialization Considerations

### What Can Be Serialized

**✅ Can be serialized:**
- Basic types (int, float, str, bool, None)
- Collections (list, tuple, dict, set)
- Functions and classes (with cloudpickle)
- NumPy arrays, pandas DataFrames
- Most Python objects

**❌ Cannot be serialized:**
- File handles and database connections
- Thread locks and synchronization primitives
- System resources (sockets, pipes)
- C extensions with special requirements

### Handling Non-Serializable Objects

```python
import sqlite3
import sitq

# Database connection (non-serializable)
def process_with_database(query):
    """Process data using database connection."""
    conn = sqlite3.connect("data.db")
    result = conn.execute(query).fetchall()
    conn.close()
    return result

# Solution 1: Create connection inside task
def process_with_database(query, db_path):
    """Process data - connection created inside task."""
    conn = sqlite3.connect(db_path)
    result = conn.execute(query).fetchall()
    conn.close()
    return result

task = sitq.Task(
    function=process_with_database,
    args=["SELECT * FROM users", "data.db"]
)

# Solution 2: Use connection factory
def create_connection(db_path):
    """Create database connection."""
    return sqlite3.connect(db_path)

def process_with_connection(query, conn_factory):
    """Process data using connection factory."""
    conn = conn_factory()
    try:
        return conn.execute(query).fetchall()
    finally:
        conn.close()

task = sitq.Task(
    function=process_with_connection,
    args=["SELECT * FROM users", lambda: create_connection("data.db")]
)
```

## Performance Optimization

### Serialization Performance

```python
import time
import pickle
import json
from dataclasses import dataclass

@dataclass
class LargeData:
    """Large data structure."""
    values: list
    metadata: dict

# Test serialization performance
data = LargeData(
    values=list(range(10000)),
    metadata={"source": "test", "version": "1.0"}
}

# Compare serializers
serializers = {
    "pickle": pickle,
    "json": json,
    "cloudpickle": __import__("cloudpickle")
}

for name, serializer in serializers.items():
    start = time.time()
    serialized = serializer.dumps(data)
    serialize_time = time.time() - start
    
    start = time.time()
    deserialized = serializer.loads(serialized)
    deserialize_time = time.time() - start
    
    print(f"{name}:")
    print(f"  Serialize: {serialize_time:.4f}s")
    print(f"  Deserialize: {deserialize_time:.4f}s")
    print(f"  Size: {len(serialized)} bytes")
```

### Compression for Large Objects

```python
import gzip
import pickle

class CompressedSerializer:
    """Serializer with compression for large objects."""
    
    def __init__(self, base_serializer=pickle, compress_threshold=1024):
        self.base_serializer = base_serializer
        self.compress_threshold = compress_threshold
    
    def dumps(self, obj):
        """Serialize with optional compression."""
        data = self.base_serializer.dumps(obj)
        if len(data) > self.compress_threshold:
            data = gzip.compress(data)
            return b"COMPRESSED:" + data
        return data
    
    def loads(self, data):
        """Deserialize with optional decompression."""
        if isinstance(data, bytes) and data.startswith(b"COMPRESSED:"):
            data = gzip.decompress(data[11:])
        return self.base_serializer.loads(data)

# Use compressed serializer
queue = sitq.TaskQueue(
    backend=sitq.SQLiteBackend(),
    serializer=CompressedSerializer()
)
```

## Security Considerations

### Safe Deserialization

```python
import pickle
import io

class SafeUnpickler(pickle.Unpickler):
    """Safe unpickler that restricts what can be loaded."""
    
    SAFE_CLASSES = {
        "builtins": {"int", "float", "str", "list", "dict", "tuple", "set"},
        "collections": {"defaultdict", "Counter", "OrderedDict"},
    }
    
    def find_class(self, module, name):
        """Restrict what classes can be unpickled."""
        if module in self.SAFE_CLASSES:
            if name in self.SAFE_CLASSES[module]:
                return super().find_class(module, name)
        raise pickle.UnpicklingError(f"Unsafe class: {module}.{name}")

class SafeSerializer:
    """Safe pickle serializer."""
    
    def dumps(self, obj):
        """Serialize object."""
        return pickle.dumps(obj)
    
    def loads(self, data):
        """Safely deserialize object."""
        return SafeUnpickler(io.BytesIO(data)).load()

# Use safe serializer
queue = sitq.TaskQueue(
    backend=sitq.SQLiteBackend(),
    serializer=SafeSerializer()
)
```

### Encryption

```python
import pickle
from cryptography.fernet import Fernet

class EncryptedSerializer:
    """Serializer with encryption."""
    
    def __init__(self, key):
        self.cipher = Fernet(key)
    
    def dumps(self, obj):
        """Encrypt and serialize object."""
        data = pickle.dumps(obj)
        return self.cipher.encrypt(data)
    
    def loads(self, data):
        """Decrypt and deserialize object."""
        data = self.cipher.decrypt(data)
        return pickle.loads(data)

# Generate encryption key
key = Fernet.generate_key()

# Use encrypted serializer
queue = sitq.TaskQueue(
    backend=sitq.SQLiteBackend(),
    serializer=EncryptedSerializer(key)
)
```

## Version Compatibility

### Handling Schema Changes

```python
import pickle
from typing import Any, Dict

class VersionedSerializer:
    """Serializer that handles version compatibility."""
    
    def __init__(self, base_serializer=pickle):
        self.base_serializer = base_serializer
        self.current_version = "1.0"
    
    def dumps(self, obj):
        """Serialize with version information."""
        data = {
            "version": self.current_version,
            "data": obj
        }
        return self.base_serializer.dumps(data)
    
    def loads(self, data):
        """Deserialize with version migration."""
        serialized_data = self.base_serializer.loads(data)
        version = serialized_data.get("version", "1.0")
        obj_data = serialized_data["data"]
        
        # Handle version migrations
        if version == "1.0":
            return self.migrate_from_1_0(obj_data)
        elif version == "1.1":
            return obj_data
        else:
            raise ValueError(f"Unsupported version: {version}")
    
    def migrate_from_1_0(self, obj_data):
        """Migrate data from version 1.0."""
        # Apply migration logic
        if isinstance(obj_data, dict) and "old_field" in obj_data:
            obj_data["new_field"] = obj_data.pop("old_field")
        return obj_data

# Use versioned serializer
queue = sitq.TaskQueue(
    backend=sitq.SQLiteBackend(),
    serializer=VersionedSerializer()
)
```

## Debugging Serialization

### Serialization Debugging

```python
import pickle
import traceback

class DebugSerializer:
    """Serializer with debugging capabilities."""
    
    def __init__(self, base_serializer=pickle):
        self.base_serializer = base_serializer
    
    def dumps(self, obj):
        """Serialize with error details."""
        try:
            return self.base_serializer.dumps(obj)
        except Exception as e:
            print(f"Serialization failed for object type: {type(obj)}")
            print(f"Error: {e}")
            traceback.print_exc()
            raise
    
    def loads(self, data):
        """Deserialize with error details."""
        try:
            return self.base_serializer.loads(data)
        except Exception as e:
            print(f"Deserialization failed")
            print(f"Data size: {len(data)} bytes")
            print(f"Error: {e}")
            traceback.print_exc()
            raise

# Use debug serializer
queue = sitq.TaskQueue(
    backend=sitq.SQLiteBackend(),
    serializer=DebugSerializer()
)
```

### Testing Serialization

```python
def test_serialization(obj, serializer):
    """Test if object can be serialized and deserialized."""
    try:
        serialized = serializer.dumps(obj)
        deserialized = serializer.loads(serialized)
        return deserialized == obj
    except Exception as e:
        print(f"Serialization test failed: {e}")
        return False

# Test various objects
test_objects = [
    42,
    "hello",
    [1, 2, 3],
    {"key": "value"},
    lambda x: x * 2,
]

for obj in test_objects:
    success = test_serialization(obj, pickle)
    print(f"{type(obj).__name__}: {'✓' if success else '✗'}")
```

## Best Practices

1. **Use cloudpickle** for maximum compatibility
2. **Test serialization** for complex objects
3. **Consider compression** for large data
4. **Use encryption** for sensitive data
5. **Handle version compatibility** for long-running systems
6. **Monitor serialization performance** for bottlenecks

## Next Steps

- [Task Queues Guide](task-queues.md) - Learn about queue management
- [Backends Guide](backends.md) - Explore storage options
- [Error Handling Guide](error-handling.md) - Comprehensive error management
- [Examples](../examples/) - Real-world serialization patterns