# Troubleshooting

This guide covers common issues, troubleshooting steps, and frequently asked questions about sitq.

## Common Issues

### Installation Problems

#### Issue: "ImportError: No module named 'sitq'"

**Symptoms:**
```python
>>> import sitq
ImportError: No module named 'sitq'
```

**Solutions:**

1. **Install sitq properly:**
   ```bash
   pip install sitq
   ```

2. **Check Python path:**
   ```bash
   python -c "import sys; print(sys.path)"
   ```

3. **Verify installation:**
   ```bash
   pip list | grep sitq
   ```

4. **Reinstall if necessary:**
   ```bash
   pip uninstall sitq
   pip install sitq
   ```

#### Issue: "SQLite backend not available"

**Symptoms:**
```python
>>> backend = sitq.SQLiteBackend("tasks.db")
AttributeError: module 'sitq' has no attribute 'SQLiteBackend'
```

**Solutions:**

1. **Check sitq version:**
   ```python
   import sitq
   print(sitq.__version__)
   ```

2. **Update to latest version:**
   ```bash
   pip install --upgrade sitq
   ```

3. **Verify backend import:**
   ```python
   from sitq.backends.sqlite import SQLiteBackend
   ```

### Runtime Issues

#### Issue: Tasks not being processed

**Symptoms:**
- Tasks remain in "queued" status
- Worker appears to be running but no progress
- Queue depth keeps increasing

**Troubleshooting Steps:**

1. **Check worker status:**
   ```python
   worker = sitq.Worker(queue)
   status = worker.get_status()
   print(f"Worker running: {status.is_running}")
   print(f"Tasks processed: {status.tasks_processed}")
   ```

2. **Verify queue connection:**
   ```python
   health = queue.health_check()
   print(f"Queue healthy: {health.is_healthy}")
   if not health.is_healthy:
       print(f"Error: {health.error_message}")
   ```

3. **Check for errors in worker:**
   ```python
   def on_error(task_id, error, retry_count):
       print(f"Task {task_id} failed: {error}")
   
   worker = sitq.Worker(queue, on_error=on_error)
   ```

4. **Test with simple task:**
   ```python
   def simple_task():
       return "Hello, World!"
   
   task = sitq.Task(function=simple_task)
   task_id = queue.enqueue(task)
   result = worker.process_task(task_id)
   print(f"Result: {result.value}")
   ```

#### Issue: Database locking errors

**Symptoms:**
```
sqlite3.OperationalError: database is locked
sqlite3.OperationalError: table tasks is locked
```

**Solutions:**

1. **Enable WAL mode:**
   ```python
   backend = sitq.SQLiteBackend(
       "tasks.db",
       enable_wal=True,
       journal_mode="WAL"
   )
   ```

2. **Configure connection pooling:**
   ```python
   backend = sitq.SQLiteBackend(
       "tasks.db",
       connection_pool_size=10,
       connection_timeout=30.0
   )
   ```

3. **Check for long-running transactions:**
   ```python
   # Avoid long-running transactions
   def process_batch(tasks):
       for task in tasks:
           result = worker.process_task(task.id)
           # Process result immediately
   ```

#### Issue: Memory usage keeps growing

**Symptoms:**
- Process memory increases over time
- System becomes slow
- Eventually runs out of memory

**Solutions:**

1. **Process tasks in batches:**
   ```python
   def process_in_batches(queue, batch_size=100):
       while True:
           tasks = queue.list_tasks(limit=batch_size)
           if not tasks:
               break
           
           for task in tasks:
               worker.process_task(task.id)
           
           # Clear references
           del tasks
   ```

2. **Use generators instead of lists:**
   ```python
   def task_generator():
       for i in range(1000):
           yield sitq.Task(function=lambda x=i: x * 2)
   
   for task in task_generator():
       task_id = queue.enqueue(task)
   ```

3. **Enable garbage collection:**
   ```python
   import gc
   
   def process_with_gc():
       # Process tasks
       for i in range(100):
           worker.process_task(task_ids[i])
           
           # Periodic garbage collection
           if i % 10 == 0:
               gc.collect()
   ```

### Performance Issues

#### Issue: Slow task processing

**Symptoms:**
- Tasks take longer than expected
- Low throughput
- High latency

**Troubleshooting Steps:**

1. **Profile task execution:**
   ```python
   import cProfile
   import pstats
   
   def profile_task():
       pr = cProfile.Profile()
       pr.enable()
       
       # Run your task
       result = worker.process_task(task_id)
       
       pr.disable()
       stats = pstats.Stats(pr)
       stats.sort_stats('cumulative')
       stats.print_stats(10)
   
   profile_task()
   ```

2. **Check serialization overhead:**
   ```python
   import time
   
   # Measure serialization time
   start = time.time()
   task_id = queue.enqueue(task)
   enqueue_time = time.time() - start
   
   start = time.time()
   result = worker.process_task(task_id)
   process_time = time.time() - start
   
   print(f"Enqueue: {enqueue_time:.3f}s")
   print(f"Process: {process_time:.3f}s")
   ```

3. **Optimize backend configuration:**
   ```python
   backend = sitq.SQLiteBackend(
       "tasks.db",
       cache_size=50000,      # Larger cache
       temp_store="MEMORY",    # Memory temp storage
       synchronous="NORMAL"    # Less strict sync
   )
   ```

#### Issue: High CPU usage

**Symptoms:**
- CPU usage consistently high
- System becomes unresponsive
- Poor performance

**Solutions:**

1. **Reduce worker count:**
   ```python
   # Use fewer workers
   worker = sitq.Worker(queue, max_workers=2)
   ```

2. **Add delays between tasks:**
   ```python
   worker = sitq.Worker(queue, poll_interval=1.0)
   ```

3. **Use CPU profiling:**
   ```python
   import psutil
   import time
   
   def monitor_cpu():
       process = psutil.Process()
       while True:
           cpu_percent = process.cpu_percent()
           print(f"CPU: {cpu_percent}%")
           time.sleep(1)
   
   # Run in separate thread
   import threading
   monitor_thread = threading.Thread(target=monitor_cpu, daemon=True)
   monitor_thread.start()
   ```

## Error Messages

### Task Errors

#### `TaskNotFoundError`
**Meaning:** Task with specified ID doesn't exist in queue.

**Common Causes:**
- Wrong task ID
- Task already completed and cleaned up
- Database corruption

**Solutions:**
```python
# Verify task exists
try:
    task = queue.get_task(task_id)
except sitq.TaskNotFoundError:
    print(f"Task {task_id} not found")
    # Check task history or re-enqueue
```

#### `TaskTimeoutError`
**Meaning:** Task execution exceeded timeout limit.

**Common Causes:**
- Task is too complex
- External service is slow
- System resources are constrained

**Solutions:**
```python
# Increase timeout
worker = sitq.Worker(queue, timeout=600.0)  # 10 minutes

# Or break down task into smaller pieces
def large_task_split(data):
    for chunk in split_data(data):
        yield process_chunk(chunk)
```

#### `TaskSerializationError`
**Meaning:** Task cannot be serialized for storage.

**Common Causes:**
- Task contains non-serializable objects
- Lambda functions with closures
- File handles or database connections

**Solutions:**
```python
# Use serializable functions
def serializable_function(data):
    return process_data(data)

# Avoid closures
# Bad: lambda x: x + external_var
# Good: def func(x, external_var): return x + external_var

# Handle non-serializable objects
def task_with_file(file_path):
    with open(file_path, 'r') as f:
        data = f.read()
    return process_data(data)  # Pass data, not file handle
```

### Queue Errors

#### `QueueFullError`
**Meaning:** Queue has reached maximum capacity.

**Common Causes:**
- Too many tasks enqueued
- Worker processing too slowly
- Memory or storage limits

**Solutions:**
```python
# Check queue capacity
stats = queue.get_stats()
print(f"Queue depth: {stats.queued_tasks}")

# Wait for space
try:
    task_id = queue.enqueue(task)
except sitq.QueueFullError:
    print("Queue full, waiting...")
    time.sleep(1)
    task_id = queue.enqueue(task)
```

#### `BackendError`
**Meaning:** Backend storage error occurred.

**Common Causes:**
- Database connection issues
- Disk space full
- Permission problems

**Solutions:**
```python
# Check backend health
health = queue.health_check()
if not health.is_healthy:
    print(f"Backend error: {health.error_message}")
    
    # Try to reconnect
    queue.backend.reconnect()
```

## Frequently Asked Questions

### General Questions

**Q: What is the difference between sitq and Celery?**

A: sitq is designed for simplicity and ease of use, while Celery is more feature-rich but complex. sitq:
- Has a simpler API
- Requires less configuration
- Is ideal for single-machine deployments
- Has built-in SQLite backend

**Q: Can I use sitq in production?**

A: Yes! sitq is production-ready with:
- ACID-compliant SQLite backend
- Comprehensive error handling
- Built-in retry mechanisms
- Monitoring and logging capabilities

**Q: How do I scale sitq?**

A: sitq can be scaled by:
- Adding more workers
- Using connection pooling
- Optimizing backend configuration
- For distributed scaling, consider using a shared database backend

### Configuration Questions

**Q: How do I configure sitq for high throughput?**

A: For high throughput:
```python
# Optimized backend
backend = sitq.SQLiteBackend(
    "tasks.db",
    connection_pool_size=20,
    enable_wal=True,
    cache_size=50000
)

# Multiple workers
workers = [
    sitq.Worker(queue, worker_id=f"worker_{i}")
    for i in range(4)
]
```

**Q: How do I secure sitq?**

A: Security measures:
```python
# Use encrypted backend
backend = sitq.SQLiteBackend(
    "tasks.db",
    encryption_key="your-secret-key"
)

# Add authentication
def authenticated_task(user_id, task_data):
    if not authenticate(user_id):
        raise PermissionError("Unauthorized")
    return process_task(task_data)
```

### Performance Questions

**Q: Why are my tasks running slowly?**

A: Common performance bottlenecks:
- Inefficient task functions
- Poor backend configuration
- Insufficient worker resources
- Network latency for external services

**Q: How do I monitor sitq performance?**

A: Monitoring options:
```python
# Built-in statistics
stats = queue.get_stats()
worker_stats = worker.get_stats()

# Custom monitoring
def monitor_performance():
    while True:
        stats = queue.get_stats()
        print(f"Queue depth: {stats.queued_tasks}")
        print(f"Throughput: {stats.tasks_per_second}")
        time.sleep(10)
```

### Troubleshooting Questions

**Q: How do I debug failing tasks?**

A: Debugging steps:
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Add error callbacks
def debug_error(task_id, error, retry_count):
    print(f"Task {task_id} failed on attempt {retry_count + 1}")
    print(f"Error: {error}")
    print(f"Traceback: {traceback.format_exc()}")

worker = sitq.Worker(queue, on_error=debug_error)
```

**Q: How do I recover from database corruption?**

A: Recovery steps:
```bash
# Check database integrity
sqlite3 tasks.db "PRAGMA integrity_check;"

# Recover from backup
cp tasks.db.backup tasks.db

# Or rebuild database
sqlite3 tasks_new.db ".restore tasks.db"
```

## Debugging Tools

### Logging Configuration

```python
import logging
import sitq

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sitq_debug.log'),
        logging.StreamHandler()
    ]
)

# Enable sitq debug logging
sitq.logger.setLevel(logging.DEBUG)
```

### Health Monitoring

```python
def comprehensive_health_check(queue, worker):
    """Perform comprehensive health check."""
    
    # Queue health
    queue_health = queue.health_check()
    print(f"Queue healthy: {queue_health.is_healthy}")
    
    # Worker health
    worker_stats = worker.get_status()
    print(f"Worker running: {worker_stats.is_running}")
    
    # System resources
    import psutil
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    
    print(f"CPU usage: {cpu_percent}%")
    print(f"Memory usage: {memory.percent}%")
    
    # Database status
    if hasattr(queue.backend, 'get_database_stats'):
        db_stats = queue.backend.get_database_stats()
        print(f"Database size: {db_stats.size_mb} MB")
        print(f"Active connections: {db_stats.active_connections}")
```

### Performance Profiling

```python
import time
import statistics
from contextlib import contextmanager

@contextmanager
def timer(name):
    """Context manager for timing operations."""
    start = time.time()
    yield
    end = time.time()
    print(f"{name}: {end - start:.3f}s")

def profile_queue_operations(queue, num_tasks=100):
    """Profile queue operations."""
    
    enqueue_times = []
    dequeue_times = []
    
    with timer("Enqueue operations"):
        for i in range(num_tasks):
            task = sitq.Task(function=lambda x=i: x * 2)
            
            start = time.time()
            task_id = queue.enqueue(task)
            enqueue_time = time.time() - start
            enqueue_times.append(enqueue_time)
    
    print(f"Average enqueue time: {statistics.mean(enqueue_times):.3f}s")
    print(f"P95 enqueue time: {statistics.quantiles(enqueue_times, n=20)[18]:.3f}s")
    
    # Similar profiling for dequeue operations
    # ...
```

## Getting Help

### Community Resources

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share experiences
- **Documentation**: Comprehensive guides and API reference
- **Examples**: Real-world usage patterns

### Support Channels

- **Documentation**: https://sitq.readthedocs.io
- **GitHub Repository**: https://github.com/username/sitq
- **Issue Tracker**: https://github.com/username/sitq/issues

### Reporting Issues

When reporting issues, include:

1. **Environment Information:**
   ```python
   import sitq
   import sys
   import platform
   
   print(f"sitq version: {sitq.__version__}")
   print(f"Python version: {sys.version}")
   print(f"Platform: {platform.platform()}")
   ```

2. **Minimal Reproducible Example:**
   ```python
   # Code that reproduces the issue
   import sitq
   
   queue = sitq.TaskQueue()
   # ... minimal code to reproduce issue
   ```

3. **Error Messages and Logs:**
   - Full error traceback
   - Relevant log entries
   - System resource usage

4. **Expected vs Actual Behavior:**
   - What you expected to happen
   - What actually happened
   - Steps to reproduce

## Best Practices

### Prevention

1. **Regular Health Checks**
   - Monitor queue and worker health
   - Set up automated alerts
   - Check system resources

2. **Proper Error Handling**
   - Always check `result.is_error`
   - Implement retry logic
   - Log errors with context

3. **Resource Management**
   - Use connection pooling
   - Monitor memory usage
   - Process tasks in batches

4. **Testing**
   - Test error scenarios
   - Load test your configuration
   - Validate backup and recovery

### Recovery Planning

1. **Backup Strategy**
   - Regular database backups
   - Off-site backup storage
   - Test recovery procedures

2. **Monitoring Alerts**
   - Error rate thresholds
   - Performance degradation alerts
   - Resource exhaustion warnings

3. **Documentation**
   - Document your configuration
   - Maintain runbooks for common issues
   - Keep contact information handy

## Next Steps

- [Contributing Guide](contributing.md) - Learn how to contribute
- [Performance Guide](performance.md) - Performance optimization
- [API Reference](../reference/api/sitq.md) - Detailed API documentation