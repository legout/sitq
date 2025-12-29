# Failure Handling

Handle task errors gracefully with comprehensive error capture and tracebacks.

## Run the Example

```bash
python examples/basic/04_failures_and_tracebacks.py
```

This example demonstrates:
1. How task failures are captured and recorded
2. Accessing error messages and tracebacks from failed tasks
3. Understanding [`Result.status`](../reference/api/sitq.core.md) values (success/failed)
4. Proper error handling in task-based workflows

View full example at [`examples/basic/04_failures_and_tracebacks.py`](../../examples/basic/04_failures_and_tracebacks.py)

## Understanding Task Results

When you retrieve a result using [`TaskQueue.get_result()`](../reference/api/sitq.queue.md), the [`Result`](../reference/api/sitq.core.md) object contains:

```python
result = await queue.get_result(task_id)

# Result properties
result.status    # "success" or "failed"
result.error     # Error message (if failed)
result.traceback # Full Python traceback (if failed)
result.value     # Serialized result value (if success)
```

## Checking Task Status

Always check the result status before accessing the value:

```python
result = await queue.get_result(task_id)

if result.status == "success":
    # Task completed successfully
    value = queue.deserialize_result(result)
    print(f"Result: {value}")
elif result.status == "failed":
    # Task failed
    print(f"Error: {result.error}")
    print(f"Traceback:\n{result.traceback}")
```

## Error Information

When a task fails, the [`Result`](../reference/api/sitq.core.md) object includes:

### Error Message
```python
result = await queue.get_result(task_id)
if result.status == "failed":
    # Human-readable error message
    print(f"Error: {result.error}")
    # Output: "Error: division by zero"
```

### Full Traceback
```python
if result.status == "failed":
    # Full Python traceback for debugging
    print(f"Traceback:\n{result.traceback}")
```

The traceback shows:
- The line number where the error occurred
- The full call stack
- All error context needed for debugging

## Common Failure Scenarios

### Division by Zero

```python
async def failing_task() -> float:
    return 1 / 0  # Raises ZeroDivisionError

task_id = await queue.enqueue(failing_task)
result = await queue.get_result(task_id)
# result.status == "failed"
# result.error == "division by zero"
```

### Custom Exceptions

```python
async def validate_item(item: str) -> str:
    if item == "invalid":
        raise KeyError(f"Invalid item: {item}")
    return f"Processed: {item}"

task_id = await queue.enqueue(validate_item, "invalid")
result = await queue.get_result(task_id)
# result.status == "failed"
# result.error == "'invalid'"
```

### Network Errors

```python
async def fetch_data(url: str) -> dict:
    response = await aiohttp.get(url)
    if response.status != 200:
        raise ConnectionError(f"HTTP {response.status}")
    return await response.json()
```

## Best Practices

### 1. Always Check Status

```python
result = await queue.get_result(task_id)

# GOOD: Check status before deserializing
if result and result.status == "success":
    value = queue.deserialize_result(result)

# BAD: Deserialize without checking
value = queue.deserialize_result(result)  # May fail!
```

### 2. Handle Timeouts

```python
try:
    result = await queue.get_result(task_id, timeout=30)
except TimeoutError:
    print("Task did not complete in time")
```

### 3. Log Errors

```python
if result.status == "failed":
    logger.error(f"Task {task_id} failed: {result.error}")
    logger.debug(f"Traceback:\n{result.traceback}")
```

### 4. Graceful Degradation

```python
result = await queue.get_result(task_id)
if result.status == "success":
    value = queue.deserialize_result(result)
else:
    # Use fallback or default value
    value = get_fallback_value(task_id)
```

## Worker Behavior

Workers continue processing other tasks after failures:

```python
# Worker processes all tasks regardless of failures
task_1 = await queue.enqueue(successful_task)
task_2 = await queue.enqueue(failing_task)
task_3 = await queue.enqueue(successful_task)

# All tasks are processed
# Task 1: success
# Task 2: failed (but doesn't crash worker)
# Task 3: success
```

## Error Recovery Strategies

### Retry Failed Tasks

```python
async def retry_task(queue, func, *args, max_retries=3):
    for attempt in range(max_retries):
        task_id = await queue.enqueue(func, *args)
        result = await queue.get_result(task_id)

        if result.status == "success":
            return queue.deserialize_result(result)

        # Log failure and retry
        logger.warning(f"Attempt {attempt + 1} failed: {result.error}")

    # All retries failed
    raise Exception(f"Task failed after {max_retries} attempts")
```

### Fallback Logic

```python
result = await queue.get_result(task_id)

if result.status == "success":
    primary_result = queue.deserialize_result(result)
else:
    logger.error(f"Primary task failed: {result.error}")
    # Use fallback task
    fallback_id = await queue.enqueue(fallback_task)
    fallback_result = await queue.get_result(fallback_id)
    primary_result = queue.deserialize_result(fallback_result)
```

## What's Next?

- [Handling Failures](../how-to/handle-failures.md) - Advanced error handling strategies
- [Getting Results](../how-to/get-results.md) - Retrieve and process results
- [Running Workers](../how-to/run-worker.md) - Configure worker behavior

## See Also

- [`Result`](../reference/api/sitq.core.md) - Result object structure
- [`TaskQueue.get_result()`](../reference/api/sitq.queue.md) - Retrieve task results
- [Error Handling](../reference/ERROR_HANDLING.md) - Sitq error types
