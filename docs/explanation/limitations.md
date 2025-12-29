# Limitations

Current limitations and constraints of sitq.

## Known Limitations

### 1. Backend Limitations

#### SQLite-Only Backend

sitq currently only supports **SQLite backend**:

**What it means:**
- No built-in PostgreSQL support
- No built-in Redis support
- No built-in NATS support
- Single-machine deployment only

**Workarounds:**
- Use SQLite in production (works well for most use cases)
- Contribute additional backend implementations
- Use external services for distributed scenarios

**Status:**
- Future versions may include additional backends
- See [GitHub Issues](https://github.com/legout/sitq/issues) for progress

#### Database Locking

SQLite has limitations on concurrent writes:

**Symptoms:**
- Database locked errors with multiple workers
- Reduced throughput under high concurrency
- Write contention

**Impact:**
- Limited concurrent write operations
- Requires WAL mode for better concurrency
- Not ideal for extremely high write loads

**Solutions:**
- Enable WAL mode: See [SQLite Backend](../how-to/sqlite-backend.md)
- Use separate databases for different workers
- Limit worker concurrency

### 2. Concurrency Limitations

#### Worker-Level Concurrency

Workers manage concurrency at process level, not distributed:

**What it means:**
- Workers in different processes can't coordinate
- No distributed task coordination
- Each worker processes independently

**Impact:**
- Tasks processed only by single worker's threads
- No automatic load balancing across workers
- Manual worker distribution required

**Workarounds:**
- Run multiple workers with same backend
- Use `max_concurrency` for thread-level parallelism
- Implement external coordination if needed

#### Global Task Ordering

Tasks are processed by workers independently:

**What it means:**
- No guaranteed global ordering across workers
- Different workers may process tasks in different order
- Priority is per-worker, not global

**Impact:**
- May affect ordered task processing requirements
- Potential for task reordering
- Not suitable for strict sequential workloads

### 3. Serialization Limitations

#### Cloudpickle Limitations

Default serializer uses cloudpickle with these constraints:

**What can be serialized:**
- Python objects (classes, functions, lambdas)
- Complex nested structures
- Custom objects with proper `__dict__`

**What cannot be serialized:**
- Database connections
- File handles, sockets
- Thread locks, semaphores
- Running asyncio tasks
- C extension objects

**Workarounds:**
- Pass file paths instead of file handles
- Close connections before task enqueue
- Use serializable wrappers

```python
# Bad: Pass file handle
async def process_file(file_handle):
    content = file_handle.read()
    return process(content)

# Good: Pass file path
async def process_file(filepath: str):
    with open(filepath, 'r') as f:
        content = f.read()
    return process(content)
```

#### Size Limitations

No built-in size limits, but practical constraints exist:

**Impact:**
- Large serialized objects consume more memory
- Slower serialization/deserialization
- Database storage overhead

**Workarounds:**
- Split large tasks into smaller chunks
- Use references (IDs, paths) instead of values
- Implement streaming for very large data

### 4. Error Handling Limitations

#### No Built-in Retry

sitq does not provide automatic retry:

**What it means:**
- Failed tasks must be manually re-queued
- No automatic retry on failure
- No exponential backoff built-in

**Impact:**
- Requires manual error handling code
- More complex error recovery logic
- Potential for lost tasks on failures

**Workarounds:**
```python
async def execute_with_retry(queue, func, *args, max_retries=3):
    """Implement retry manually."""
    last_error = None
    
    for attempt in range(max_retries):
        try:
            task_id = await queue.enqueue(func, *args)
            result = await queue.get_result(task_id)
            
            if result and result.status == "success":
                return queue.deserialize_result(result)
        
        except Exception as e:
            last_error = e
            await asyncio.sleep(2 ** attempt)
    
    # All retries failed
    raise last_error
```

#### Limited Error Context

Error information is captured but may be incomplete:

**What's included:**
- Exception type
- Error message
- Full traceback

**What's not included:**
- Task arguments (for debugging)
- Worker ID that processed task
- Execution duration
- Resource usage during execution

**Workarounds:**
- Log task details before enqueue
- Use error callbacks (if implemented)
- Monitor worker logs

### 5. Performance Limitations

#### No Built-in Monitoring

sitq does not provide built-in performance metrics:

**What's missing:**
- Task throughput metrics
- Queue depth monitoring
- Worker utilization tracking
- Automatic performance alerts

**Workarounds:**
- Implement custom logging
- Use external monitoring tools
- Track metrics manually

```python
import time
from collections import defaultdict

class TaskMonitor:
    """Manual task monitoring."""
    
    def __init__(self):
        self.stats = defaultdict(int)
    
    async def enqueue(self, func, *args):
        start = time.time()
        task_id = await queue.enqueue(func, *args)
        enqueue_time = time.time() - start
        self.stats['enqueue_count'] += 1
        self.stats['enqueue_time'] += enqueue_time
        return task_id
    
    async def get_result(self, task_id):
        start = time.time()
        result = await queue.get_result(task_id)
        wait_time = time.time() - start
        if result:
            self.stats[f"status_{result.status}"] += 1
        self.stats['wait_time'] += wait_time
        return result

monitor = TaskMonitor()
```

#### Polling Overhead

Workers poll for tasks (not event-driven):

**Impact:**
- Additional latency (up to `poll_interval` seconds)
- CPU usage for idle workers
- Reduced efficiency at low task rates

**Workarounds:**
- Use short `poll_interval` for responsiveness
- Increase `max_concurrency` to reduce idle polling
- Consider event-driven backends (future)

### 6. Operational Limitations

#### No Built-in Admin

No built-in administrative tools:

**What's missing:**
- Task inspection/pausing
- Queue management interface
- Worker control API
- Backup/restore tools

**Workarounds:**
- Use database directly for admin operations
- Implement custom admin tools
- Leverage SQLite tools

```bash
# Direct database inspection
sqlite3 tasks.db "SELECT * FROM tasks LIMIT 10;"

# Backup database
cp tasks.db tasks_backup_$(date +%Y%m%d).db
```

#### Manual Worker Management

Workers must be managed manually:

**Impact:**
- No worker pool management
- No automatic worker scaling
- Manual worker lifecycle control

**Workarounds:**
- Implement external process management
- Use systemd/supervisor for production
- Create custom worker manager

### 7. Feature Limitations

#### No Task Prioritization

Tasks are processed FIFO (first-in, first-out):

**What it means:**
- No built-in priority queue
- All tasks have equal priority
- No task weighting

**Workarounds:**
- Enqueue high-priority tasks first
- Use separate queues for different priorities
- Implement custom priority logic

```python
async def enqueue_with_priority(queue, tasks, priority_key="priority"):
    """Enqueue tasks by priority manually."""
    # Sort by priority
    sorted_tasks = sorted(tasks, key=lambda t: t.get(priority_key, 0))
    
    # Enqueue in priority order
    task_ids = []
    for task in sorted_tasks:
        task_id = await queue.enqueue(task['func'], *task['args'])
        task_ids.append(task_id)
    
    return task_ids
```

#### No Task Dependencies

Cannot specify task dependencies:

**What it means:**
- Tasks execute independently
- No DAG (directed acyclic graph) support
- No guaranteed execution order for dependent tasks

**Workarounds:**
- Implement dependency management manually
- Use external orchestration tools
- Split workflows into independent stages

```python
async def execute_workflow(queue, stages):
    """Execute dependent tasks manually."""
    previous_results = {}
    
    for stage in stages:
        # Wait for dependencies
        if stage['depends_on']:
            for dep in stage['depends_on']:
                await asyncio.sleep(0.1)  # Poll for completion
        
        # Execute current stage
        task_id = await queue.enqueue(
            stage['func'],
            *[previous_results[d] for d in stage['depends_on']]
        )
        
        result = await queue.get_result(task_id)
        previous_results[stage['name']] = queue.deserialize_result(result)
```

### 8. Platform Limitations

#### Python 3.13+ Required

sitq requires Python 3.13 or higher:

**Impact:**
- Not compatible with older Python versions
- Requires Python 3.13+ in production
- May limit deployment options

**Workarounds:**
- Upgrade Python environment
- Use Docker with Python 3.13
- Use virtual environments

#### Async-Only Architecture

sitq is async-first:

**What it means:**
- Primary API is async
- Sync support is a wrapper, not native
- Worker execution is async

**Impact:**
- Requires async/await patterns
- More complex than synchronous APIs
- Different programming paradigm for some users

**Benefits:**
- Better performance for I/O tasks
- Native concurrency support
- Modern Python patterns

### 9. Security Limitations

#### No Built-in Security

No built-in security features:

**What's missing:**
- Task authentication
- Worker authentication
- Encryption at rest
- Audit logging

**Workarounds:**
- Use database-level security (file permissions, encryption)
- Implement network security (TLS, VPNs)
- Use custom serializers for encryption

```python
from sitq.serialization import Serializer

class EncryptedSerializer(Serializer):
    """Add encryption to serialization."""
    
    def __init__(self, key):
        from cryptography.fernet import Fernet
        self.cipher = Fernet(key)
    
    def dumps(self, obj) -> bytes:
        import pickle
        data = pickle.dumps(obj)
        return self.cipher.encrypt(data)
    
    def loads(self, data: bytes):
        decrypted = self.cipher.decrypt(data)
        import pickle
        return pickle.loads(decrypted)

# Use with queue
key = Fernet.generate_key()
serializer = EncryptedSerializer(key)
queue = TaskQueue(backend=backend, serializer=serializer)
```

## When to Consider Alternatives

Consider alternative task queue libraries when:

1. **Distributed Processing Needed**
   - Redis/PostgreSQL backends required
   - Multi-machine deployment
   - Global task coordination

2. **Complex Scheduling Required**
   - Cron-like scheduling
   - Task dependencies
   - Complex workflows

3. **Enterprise Features Required**
   - Built-in monitoring
   - Administrative tools
   - Advanced security

4. **Large-Scale Operations**
   - >10,000 tasks/hour
   - High-concurrency distributed workers
   - Complex retry policies

5. **Language Constraints**
   - Cannot use Python 3.13+
   - Require sync-native API
   - Want Java/Go/etc. clients

## Addressing Limitations

### Contributing Improvements

Many limitations can be addressed by contributing:

1. **Additional Backends**: Implement PostgreSQL, Redis, NATS backends
2. **Retry Logic**: Add automatic retry with exponential backoff
3. **Monitoring**: Add built-in metrics and monitoring
4. **Admin Tools**: Create task inspection and queue management
5. **Priority Queues**: Implement task prioritization
6. **Task Dependencies**: Add DAG support for workflows

### Feature Requests

Request features on GitHub:
- [Issues](https://github.com/legout/sitq/issues) - Report bugs and request features
- [Discussions](https://github.com/legout/sitq/discussions) - Discuss ideas
- [Pull Requests](https://github.com/legout/sitq/pulls) - Contribute implementations

## Best Practices Within Limitations

### 1. Plan for Scale

- Design for single-machine deployment initially
- Plan migration strategy if scaling needed
- Monitor for hitting limitations early

### 2. Implement Workarounds

- Use workarounds proactively (retry, priority logic)
- Build custom tools for missing features (monitoring)
- Consider architecture that works within constraints

### 3. Monitor Performance

- Track task processing times
- Monitor queue depth
- Watch for lock contention

### 4. Test Thoroughly

- Test with realistic workloads
- Stress test concurrency limits
- Verify error handling under failure

## What's Next?

- [Architecture](architecture.md) - System design
- [Serialization](serialization.md) - How serialization works
- [Contributing](../how-to/contributing.md) - How to improve sitq

## See Also

- [GitHub Issues](https://github.com/legout/sitq/issues) - Track limitations
- [Roadmap](https://github.com/legout/sitq/tree/main/openspec/specs/) - Future plans
- [How-to Guides](../how-to/installation.md) - Practical solutions
