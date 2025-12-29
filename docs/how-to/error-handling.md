# Error Handling

Robust error handling is crucial for building reliable task processing systems. sitq provides comprehensive error handling at every level of the architecture.

## Error Types

### Core Exceptions

```python
import sitq

# Task-related errors
sitq.TaskNotFoundError          # Task doesn't exist
sitq.TaskSerializationError    # Cannot serialize/deserialize task
sitq.TaskTimeoutError           # Task execution timed out
sitq.TaskRetryExhaustedError    # All retries exhausted

# Queue-related errors
sitq.QueueFullError             # Queue is at capacity
sitq.QueueEmptyError            # Queue is empty
sitq.QueueClosedError           # Queue is closed

# Backend errors
sitq.BackendError               # General backend error
sitq.BackendConnectionError     # Cannot connect to backend
sitq.BackendTimeoutError        # Backend operation timed out

# Worker errors
sitq.WorkerError                # General worker error
sitq.WorkerStoppedError         # Worker is stopped
sitq.WorkerBusyError            # Worker is busy
```

## Task Error Handling

### Basic Error Handling

```python
import sitq

def risky_task(data):
    """Task that might fail."""
    if data < 0:
        raise ValueError("Data cannot be negative")
    return data * 2

queue = sitq.TaskQueue(backend=sitq.SQLiteBackend(":memory:"))
worker = sitq.Worker(queue)

# Create task that will fail
task = sitq.Task(function=risky_task, args=[-5])
task_id = queue.enqueue(task)

# Process with error handling
try:
    result = worker.process_task(task_id)
    if result.is_error:
        print(f"Task failed: {result.error}")
        print(f"Error type: {type(result.error)}")
    else:
        print(f"Task succeeded: {result.value}")
except sitq.TaskNotFoundError:
    print("Task not found in queue")
except sitq.WorkerError as e:
    print(f"Worker error: {e}")
```

### Retry Configuration

```python
# Task with retry configuration
task = sitq.Task(
    function=risky_task,
    args=[-5],
    max_retries=3,              # Retry up to 3 times
    retry_delay=1.0,            # Wait 1 second between retries
    backoff_factor=2.0          # Exponential backoff
)

task_id = queue.enqueue(task)
result = worker.process_task(task_id)

print(f"Final result: {result.is_error}")
print(f"Retry count: {result.retry_count}")
```

### Custom Retry Logic

```python
def custom_retry_condition(error, retry_count):
    """Custom condition for retrying."""
    # Retry on ValueError but not on TypeError
    if isinstance(error, ValueError):
        return retry_count < 5
    return False

# Task with custom retry logic
task = sitq.Task(
    function=risky_task,
    args=[-5],
    retry_condition=custom_retry_condition
)
```

## Queue Error Handling

### Queue Operation Errors

```python
try:
    # Enqueue task
    task_id = queue.enqueue(task)
except sitq.QueueFullError:
    print("Queue is full, try again later")
except sitq.TaskSerializationError as e:
    print(f"Cannot serialize task: {e}")
except sitq.BackendError as e:
    print(f"Backend error: {e}")

try:
    # Get result
    result = queue.get_result(task_id, timeout=30.0)
except sitq.TaskNotFoundError:
    print("Task not found")
except sitq.TaskTimeoutError:
    print("Task timed out")
except sitq.BackendTimeoutError:
    print("Backend operation timed out")
```

### Queue Health Monitoring

```python
# Check queue health
health = queue.health_check()
if not health.is_healthy:
    print(f"Queue unhealthy: {health.error_message}")
    print(f"Backend status: {health.backend_status}")
    print(f"Queue size: {health.queue_size}")

# Monitor queue metrics
metrics = queue.get_metrics()
print(f"Success rate: {metrics.success_rate:.2%}")
print(f"Error rate: {metrics.error_rate:.2%}")
print(f"Average wait time: {metrics.avg_wait_time}s")
```

## Worker Error Handling

### Worker Error Callbacks

```python
def on_task_error(task_id, error, retry_count):
    """Called when a task fails."""
    print(f"❌ Task {task_id} failed (attempt {retry_count + 1}): {error}")
    
    # Log to external system
    log_error(task_id, error, retry_count)

def on_task_success(task_id, result):
    """Called when a task succeeds."""
    print(f"✅ Task {task_id} succeeded: {result}")

def on_worker_error(worker_id, error):
    """Called when worker encounters error."""
    print(f"🔥 Worker {worker_id} error: {error}")

# Worker with error callbacks
worker = sitq.Worker(
    queue=queue,
    on_error=on_task_error,
    on_success=on_task_success,
    on_worker_error=on_worker_error
)
```

### Graceful Error Recovery

```python
class ResilientWorker(sitq.Worker):
    """Worker with enhanced error recovery."""
    
    def __init__(self, queue, **kwargs):
        super().__init__(queue, **kwargs)
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
    
    def process_task(self, task_id):
        """Process task with error recovery."""
        try:
            result = super().process_task(task_id)
            self.consecutive_errors = 0  # Reset on success
            return result
        except Exception as e:
            self.consecutive_errors += 1
            
            if self.consecutive_errors >= self.max_consecutive_errors:
                print(f"Too many consecutive errors: {self.consecutive_errors}")
                self.pause_worker(30.0)  # Pause for 30 seconds
                self.consecutive_errors = 0
            
            raise
    
    def pause_worker(self, duration):
        """Pause worker for specified duration."""
        print(f"Pausing worker for {duration} seconds")
        time.sleep(duration)

# Use resilient worker
worker = ResilientWorker(queue)
```

## Backend Error Handling

### Connection Error Handling

```python
class RobustSQLiteBackend(sitq.SQLiteBackend):
    """SQLite backend with robust error handling."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retries = 3
        self.retry_delay = 1.0
    
    def execute_with_retry(self, operation, *args, **kwargs):
        """Execute database operation with retry."""
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except sitq.BackendConnectionError as e:
                if attempt == self.max_retries - 1:
                    raise
                print(f"Connection failed (attempt {attempt + 1}): {e}")
                time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
    
    def store_task(self, task):
        """Store task with retry."""
        return self.execute_with_retry(super().store_task, task)
    
    def get_task(self, task_id):
        """Get task with retry."""
        return self.execute_with_retry(super().get_task, task_id)

# Use robust backend
backend = RobustSQLiteBackend("tasks.db")
queue = sitq.TaskQueue(backend=backend)
```

### Backend Health Monitoring

```python
def monitor_backend_health(backend, interval=60):
    """Monitor backend health periodically."""
    while True:
        try:
            health = backend.health_check()
            if not health.is_healthy:
                print(f"⚠️ Backend unhealthy: {health.error_message}")
                send_alert(f"Backend health issue: {health.error_message}")
            
            # Log metrics
            metrics = backend.get_metrics()
            print(f"Backend metrics: {metrics}")
            
        except Exception as e:
            print(f"Health monitoring error: {e}")
            send_alert(f"Health monitoring failed: {e}")
        
        time.sleep(interval)

# Start health monitoring (in background thread)
import threading
monitor_thread = threading.Thread(
    target=monitor_backend_health,
    args=(backend,),
    daemon=True
)
monitor_thread.start()
```

## Global Error Handling

### Error Logging

```python
import logging
import traceback

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sitq_errors.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("sitq")

def log_error(error, context=None):
    """Log error with context."""
    error_info = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "context": context or {}
    }
    logger.error(f"Error occurred: {error_info}")

# Use in error callbacks
def on_error(task_id, error, retry_count):
    """Enhanced error callback."""
    log_error(error, {
        "task_id": task_id,
        "retry_count": retry_count,
        "timestamp": time.time()
    })
```

### Error Recovery Strategies

```python
class ErrorRecoveryManager:
    """Manages error recovery strategies."""
    
    def __init__(self, queue):
        self.queue = queue
        self.recovery_strategies = {}
    
    def register_strategy(self, error_type, strategy):
        """Register recovery strategy for error type."""
        self.recovery_strategies[error_type] = strategy
    
    def handle_error(self, task_id, error):
        """Handle error with appropriate strategy."""
        error_type = type(error)
        
        if error_type in self.recovery_strategies:
            strategy = self.recovery_strategies[error_type]
            return strategy(task_id, error)
        else:
            # Default strategy
            return self.default_recovery(task_id, error)
    
    def default_recovery(self, task_id, error):
        """Default recovery strategy."""
        print(f"Using default recovery for task {task_id}: {error}")
        # Log error and continue
        return False  # Don't retry

# Set up recovery manager
recovery = ErrorRecoveryManager(queue)

# Register custom strategies
recovery.register_strategy(ValueError, lambda tid, err: True)  # Retry
recovery.register_strategy(TypeError, lambda tid, err: False)  # Don't retry

# Use in worker
def on_task_error(task_id, error, retry_count):
    """Error callback with recovery."""
    should_retry = recovery.handle_error(task_id, error)
    return should_retry
```

## Testing Error Handling

### Error Injection

```python
class ErrorInjectingWorker(sitq.Worker):
    """Worker that can inject errors for testing."""
    
    def __init__(self, queue, error_config=None, **kwargs):
        super().__init__(queue, **kwargs)
        self.error_config = error_config or {}
    
    def process_task(self, task_id):
        """Process task with optional error injection."""
        task = self.queue.get_task(task_id)
        
        # Check if we should inject an error
        if task_id in self.error_config:
            error_type = self.error_config[task_id]
            if error_type == "timeout":
                raise sitq.TaskTimeoutError("Injected timeout")
            elif error_type == "serialization":
                raise sitq.TaskSerializationError("Injected serialization error")
            elif error_type == "backend":
                raise sitq.BackendError("Injected backend error")
        
        return super().process_task(task_id)

# Test error handling
error_config = {
    "task_1": "timeout",
    "task_2": "serialization",
    "task_3": "backend"
}

worker = ErrorInjectingWorker(queue, error_config=error_config)
```

### Error Scenario Testing

```python
def test_error_scenarios():
    """Test various error scenarios."""
    scenarios = [
        ("Task not found", lambda: worker.process_task("nonexistent")),
        ("Queue full", lambda: fill_queue_and_enqueue()),
        ("Backend timeout", lambda: simulate_backend_timeout()),
        ("Serialization error", lambda: enqueue_non_serializable()),
    ]
    
    for scenario_name, scenario_func in scenarios:
        try:
            scenario_func()
            print(f"❌ {scenario_name}: Expected error but got success")
        except Exception as e:
            print(f"✅ {scenario_name}: Correctly handled {type(e).__name__}")

test_error_scenarios()
```

## Best Practices

1. **Always check `result.is_error`** after task processing
2. **Use appropriate retry policies** for different error types
3. **Implement comprehensive logging** for debugging
4. **Monitor system health** continuously
5. **Test error scenarios** thoroughly
6. **Use graceful degradation** when possible
7. **Set timeouts** to prevent hanging operations

## Next Steps

- [Task Queues Guide](task-queues.md) - Learn about queue management
- [Workers Guide](workers.md) - Explore task execution
- [Backends Guide](backends.md) - Understand storage options
- [Examples](../examples/) - Real-world error handling patterns