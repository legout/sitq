# Handling Failures

Handle task errors gracefully with comprehensive error capture and recovery strategies.

## Checking Task Status

Always check result status before processing:

```python
result = await queue.get_result(task_id)

if result is None:
    # Task doesn't exist
    print(f"Task {task_id} not found")
elif result.status == "success":
    # Task completed successfully
    value = queue.deserialize_result(result)
    print(f"Result: {value}")
elif result.status == "failed":
    # Task failed
    print(f"Error: {result.error}")
    print(f"Traceback:\n{result.traceback}")
```

## Accessing Error Information

### Error Message

```python
result = await queue.get_result(task_id)

if result and result.status == "failed":
    # Human-readable error message
    print(f"Error: {result.error}")
```

### Full Traceback

```python
result = await queue.get_result(task_id)

if result and result.status == "failed":
    # Complete Python traceback
    print("Traceback:")
    print(result.traceback)
```

### Traceback Lines

```python
if result and result.status == "failed":
    # Get last 5 lines of traceback
    traceback_lines = result.traceback.split("\n")
    for line in traceback_lines[-5:]:
        if line.strip():
            print(line)
```

## Common Error Scenarios

### Division by Zero

```python
async def divide_numbers(a: int, b: int) -> float:
    return a / b

task_id = await queue.enqueue(divide_numbers, 10, 0)
result = await queue.get_result(task_id)

# result.status == "failed"
# result.error == "division by zero"
```

### Missing Files

```python
async def read_file(filepath: str) -> str:
    with open(filepath, "r") as f:
        return f.read()

task_id = await queue.enqueue(read_file, "/nonexistent.txt")
result = await queue.get_result(task_id)

# result.status == "failed"
# result.error contains FileNotFoundError message
```

### Network Errors

```python
async def fetch_url(url: str) -> str:
    import aiohttp
    async with aiohttp.get(url) as response:
        return await response.text()

task_id = await queue.enqueue(fetch_url, "http://invalid.url")
result = await queue.get_result(task_id)

# result.status == "failed"
# result.error contains connection error
```

## Error Recovery Strategies

### Retry Logic

```python
async def retry_task(queue, func, *args, max_retries=3, **kwargs):
    """Retry task on failure."""
    for attempt in range(max_retries):
        task_id = await queue.enqueue(func, *args, **kwargs)
        
        # Wait for result
        while True:
            result = await queue.get_result(task_id)
            if result:
                break
            await asyncio.sleep(0.1)
        
        if result.status == "success":
            return queue.deserialize_result(result)
        
        # Log failure and retry
        print(f"Attempt {attempt + 1} failed: {result.error}")
        await asyncio.sleep(1)  # Wait before retry
    
    # All retries failed
    raise Exception(f"Task failed after {max_retries} attempts")
```

### Fallback Value

```python
async def get_result_with_fallback(task_id, default=None):
    """Get result with fallback value."""
    result = await queue.get_result(task_id)
    
    if result and result.status == "success":
        return queue.deserialize_result(result)
    
    # Use default if failed or missing
    return default

# Use fallback
value = await get_result_with_fallback(task_id, default="default_value")
```

### Graceful Degradation

```python
async def process_with_fallback(primary_task, fallback_task, *args):
    """Try primary task, fallback on failure."""
    
    # Try primary
    task_id = await queue.enqueue(primary_task, *args)
    result = await queue.get_result(task_id)
    
    if result and result.status == "success":
        return queue.deserialize_result(result)
    
    # Log primary failure
    print(f"Primary task failed: {result.error}")
    
    # Use fallback
    fallback_id = await queue.enqueue(fallback_task, *args)
    fallback_result = await queue.get_result(fallback_id)
    
    if fallback_result and fallback_result.status == "success":
        return queue.deserialize_result(fallback_result)
    
    # Both failed
    raise Exception("Primary and fallback tasks failed")
```

## Error Logging

### Log Errors

```python
from loguru import logger

async def process_with_logging(task_id):
    """Process task with error logging."""
    result = await queue.get_result(task_id)
    
    if result:
        if result.status == "success":
            logger.info(f"Task {task_id} succeeded")
        else:
            logger.error(f"Task {task_id} failed: {result.error}")
            logger.debug(f"Traceback:\n{result.traceback}")
    
    return result
```

### Structured Logging

```python
async def log_task_result(task_id, queue):
    """Log task result with structured format."""
    result = await queue.get_result(task_id)
    
    log_data = {
        "task_id": task_id,
        "status": result.status if result else "not_found",
        "error": result.error if result else None,
        "success": result.status == "success" if result else False
    }
    
    if log_data["success"]:
        logger.info("Task succeeded", **log_data)
    else:
        logger.error("Task failed", **log_data)
    
    return result
```

## Worker Error Handling

### Workers Continue After Failures

Workers continue processing other tasks after a failure:

```python
# Enqueue multiple tasks
task_ids = []
task_ids.append(await queue.enqueue(successful_task))
task_ids.append(await queue.enqueue(failing_task))
task_ids.append(await queue.enqueue(successful_task))

# Worker processes all tasks
# Task 1: success
# Task 2: failed (but worker continues)
# Task 3: success
```

### Monitoring Failure Rates

```python
async def track_failures(task_ids, queue):
    """Track success/failure rates."""
    successes = 0
    failures = 0
    
    for task_id in task_ids:
        result = await queue.get_result(task_id)
        
        if result and result.status == "success":
            successes += 1
        elif result:
            failures += 1
    
    total = successes + failures
    if total > 0:
        success_rate = (successes / total) * 100
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Failures: {failures}/{total}")
```

## Best Practices

1. **Always check status** before deserializing
2. **Log errors** with tracebacks for debugging
3. **Implement retry logic** for transient failures
4. **Use fallback values** for non-critical tasks
5. **Monitor failure rates** in production
6. **Handle specific errors** differently based on type

## Error Recovery Examples

### Retry with Exponential Backoff

```python
async def retry_with_backoff(task_id, max_retries=5):
    """Retry with exponential backoff."""
    for attempt in range(max_retries):
        result = await queue.get_result(task_id)
        
        if result and result.status == "success":
            return queue.deserialize_result(result)
        
        # Exponential backoff: 1s, 2s, 4s, 8s, 16s
        backoff = 2 ** attempt
        print(f"Attempt {attempt + 1} failed, retrying in {backoff}s")
        await asyncio.sleep(backoff)
    
    raise Exception(f"Failed after {max_retries} retries")
```

### Circuit Breaker Pattern

```python
class CircuitBreaker:
    """Stop trying after repeated failures."""
    
    def __init__(self, threshold=5, timeout=60):
        self.failures = 0
        self.threshold = threshold
        self.timeout = timeout
        self.last_failure = None
    
    async def execute(self, queue, func, *args, **kwargs):
        """Execute with circuit breaker."""
        # Check if circuit is open
        if (self.failures >= self.threshold and 
            self.last_failure and 
            asyncio.get_event_loop().time() - self.last_failure < self.timeout):
            raise Exception("Circuit breaker is open")
        
        # Try to execute
        task_id = await queue.enqueue(func, *args, **kwargs)
        result = await queue.get_result(task_id)
        
        if result and result.status == "success":
            # Reset on success
            self.failures = 0
            return queue.deserialize_result(result)
        else:
            # Increment failure count
            self.failures += 1
            self.last_failure = asyncio.get_event_loop().time()
            raise Exception(f"Task failed: {result.error}")
```

## What's Next?

- [Failure Handling Tutorial](../tutorials/failures.md) - Learn error handling in depth
- [Getting Results](get-results.md) - Retrieve task results
- [Error Handling Reference](error-handling.md) - Comprehensive error management

## See Also

- [`Result`](../reference/api/sitq.core.md) - Result object with error/traceback
- [Error Handling](../reference/ERROR_HANDLING.md) - Sitq error types
