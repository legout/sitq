# Getting Results

Retrieve task results from the queue with proper error handling and timeout management.

## Basic Result Retrieval

Get a task result by ID:

```python
from sitq import TaskQueue, SQLiteBackend

backend = SQLiteBackend("tasks.db")
queue = TaskQueue(backend=backend)

# Enqueue a task
task_id = await queue.enqueue(my_function, "arg1", "arg2")

# Get result
result = await queue.get_result(task_id)

if result and result.status == "success":
    # Task succeeded
    value = queue.deserialize_result(result)
    print(f"Result: {value}")
elif result:
    # Task failed
    print(f"Error: {result.error}")
else:
    # Result not found
    print("Task not found")
```

## Result Properties

The [`Result`](../reference/api/sitq.core.md) object contains:

```python
result = await queue.get_result(task_id)

# Status: "success" or "failed"
print(result.status)

# Error message (if failed)
if result.error:
    print(result.error)

# Traceback (if failed)
if result.traceback:
    print(result.traceback)

# Serialized value (if success)
if result.value:
    value = queue.deserialize_result(result)
    print(value)
```

## Timeouts

Prevent hanging with timeout:

```python
# Wait up to 30 seconds
result = await queue.get_result(task_id, timeout=30)

if result is None:
    print("Task timed out")
elif result.status == "success":
    value = queue.deserialize_result(result)
    print(f"Result: {value}")
```

### Choosing Timeouts

```python
# Quick tasks (e.g., API calls)
result = await queue.get_result(task_id, timeout=5)

# Medium tasks (e.g., file processing)
result = await queue.get_result(task_id, timeout=60)

# Long-running tasks (e.g., data analysis)
result = await queue.get_result(task_id, timeout=300)
```

## Deserializing Results

Always deserialize after checking status:

```python
result = await queue.get_result(task_id)

# Check status first
if result and result.status == "success":
    # Safe to deserialize
    value = queue.deserialize_result(result)
    print(f"Result: {value}")
```

### Why Deserialize?

Results are serialized using cloudpickle. You must deserialize to get the actual Python object:

```python
result = await queue.get_result(task_id)

# Without deserializing
print(result.value)  # Returns: b'\x80\x04...' (bytes)

# With deserializing
value = queue.deserialize_result(result)
print(value)  # Returns: 'Hello, World!'
```

## Polling for Results

Wait for results iteratively:

```python
async def wait_for_result(task_id, timeout=30):
    """Poll for result until available or timeout."""
    start_time = asyncio.get_event_loop().time()
    
    while asyncio.get_event_loop().time() - start_time < timeout:
        result = await queue.get_result(task_id)
        
        if result is None:
            # Task not found
            return None
        elif result.status in ["success", "failed"]:
            # Task complete
            return result
        
        # Task still pending, wait and retry
        await asyncio.sleep(0.5)
    
    # Timeout
    return None

# Use polling function
result = await wait_for_result(task_id, timeout=10)
if result and result.status == "success":
    value = queue.deserialize_result(result)
    print(f"Result: {value}")
```

## Batch Result Retrieval

Get multiple results:

```python
async def get_all_results(task_ids, timeout=30):
    """Get results for multiple task IDs."""
    results = {}
    
    for task_id in task_ids:
        result = await queue.get_result(task_id, timeout=timeout)
        if result:
            results[task_id] = result
    
    return results

# Enqueue multiple tasks
task_ids = []
for i in range(5):
    task_id = await queue.enqueue(my_function, i)
    task_ids.append(task_id)

# Get all results
results = await get_all_results(task_ids)

for task_id, result in results.items():
    if result.status == "success":
        value = queue.deserialize_result(result)
        print(f"Task {task_id}: {value}")
    else:
        print(f"Task {task_id} failed: {result.error}")
```

## Error Handling

### Task Not Found

```python
result = await queue.get_result(task_id)

if result is None:
    # Task doesn't exist
    print(f"Task {task_id} not found")
```

### Task Failed

```python
result = await queue.get_result(task_id)

if result and result.status == "failed":
    # Task execution failed
    print(f"Error: {result.error}")
    print(f"Traceback:\n{result.traceback}")
```

### Timeout

```python
try:
    result = await queue.get_result(task_id, timeout=5)
except asyncio.TimeoutError:
    print("Result retrieval timed out")
```

## Common Patterns

### Immediate Result Check

Check if task is complete before waiting:

```python
result = await queue.get_result(task_id)

if result is None:
    print("Task not found")
elif result.status == "success":
    value = queue.deserialize_result(result)
    print(f"Result: {value}")
elif result.status == "failed":
    print(f"Error: {result.error}")
else:
    print("Task still pending")
```

### Retry on Timeout

```python
async def get_result_with_retry(task_id, max_retries=3):
    """Get result with retries on timeout."""
    for attempt in range(max_retries):
        result = await queue.get_result(task_id, timeout=10)
        
        if result:
            return result
        
        # Wait before retry
        await asyncio.sleep(2)
    
    return None

result = await get_result_with_retry(task_id)
if result:
    value = queue.deserialize_result(result)
    print(f"Result: {value}")
else:
    print("Max retries reached")
```

### Result with Default Value

Provide fallback for missing or failed results:

```python
async def get_result_safe(task_id, default=None):
    """Get result with fallback."""
    result = await queue.get_result(task_id)
    
    if result and result.status == "success":
        return queue.deserialize_result(result)
    
    # Use default if failed or missing
    return default

# Use with fallback
value = await get_result_safe(task_id, default="fallback_value")
print(f"Result: {value}")
```

## Best Practices

1. **Always check status** before deserializing
2. **Use appropriate timeouts** to prevent hanging
3. **Handle None results** for missing tasks
4. **Log errors** with tracebacks for debugging
5. **Use polling** for long-running tasks with status checks

## What's Next?

- [Failure Handling](handle-failures.md) - Handle task errors gracefully
- [Running Workers](run-worker.md) - Worker configuration and management
- [Error Handling](error-handling.md) - Comprehensive error management

## See Also

- [`Result`](../reference/api/sitq.core.md) - Result object structure
- [`TaskQueue.get_result()`](../reference/api/sitq.queue.md) - API reference
- [`TaskQueue.deserialize_result()`](../reference/api/sitq.queue.md) - Deserialization
