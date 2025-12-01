# Backends

Backends provide persistent storage for tasks and results in sitq. The backend you choose depends on your scalability, performance, and reliability requirements.

## Available Backends

### SQLite Backend (Default)

SQLite is the default backend, perfect for most applications:

```python
import sitq

# File-based SQLite (persistent)
backend = sitq.SQLiteBackend("tasks.db")
queue = sitq.TaskQueue(backend=backend)

# In-memory SQLite (for testing)
backend = sitq.SQLiteBackend(":memory:")
queue = sitq.TaskQueue(backend=backend)
```

**Pros:**
- No external dependencies
- ACID compliant
- Easy to set up
- Good performance for most workloads

**Cons:**
- Limited to single-machine deployment
- Not suitable for high-concurrency scenarios

## SQLite Backend Configuration

### Basic Configuration

```python
# Simple SQLite backend
backend = sitq.SQLiteBackend("production.db")

# With custom settings
backend = sitq.SQLiteBackend(
    database="production.db",
    connection_pool_size=10,
    connection_timeout=30.0,
    enable_wal=True,          # Enable Write-Ahead Logging
    checkpoint_interval=1000  # Checkpoint interval for WAL
)
```

### Performance Optimization

```python
# High-performance SQLite configuration
backend = sitq.SQLiteBackend(
    database="high_volume.db",
    connection_pool_size=20,
    max_overflow=10,
    connection_timeout=60.0,
    enable_wal=True,
    synchronous="NORMAL",     # Balance between safety and performance
    cache_size=10000,         # Cache size in pages
    temp_store="MEMORY"       # Store temporary tables in memory
)
```

### Connection Pooling

```python
# Configure connection pooling
backend = sitq.SQLiteBackend(
    database="pooled.db",
    connection_pool_size=15,  # Base pool size
    max_overflow=5,           # Additional connections when needed
    pool_timeout=30.0,        # Timeout for getting connection
    pool_recycle=3600.0       # Recycle connections every hour
)
```

## Backend Operations

### Database Schema

The SQLite backend creates the following tables:

```sql
-- Tasks table
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    function BLOB NOT NULL,
    args BLOB,
    kwargs BLOB,
    priority INTEGER DEFAULT 0,
    status TEXT DEFAULT 'queued',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 0,
    error_message TEXT
);

-- Results table
CREATE TABLE results (
    task_id TEXT PRIMARY KEY,
    value BLOB,
    is_error BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

### Custom Backend Implementation

```python
import sitq
from sitq.backends.base import BaseBackend

class CustomBackend(BaseBackend):
    """Custom backend implementation."""
    
    def __init__(self, config):
        self.config = config
        self.initialize()
    
    def initialize(self):
        """Initialize backend storage."""
        # Set up your storage system
        pass
    
    def store_task(self, task):
        """Store a task."""
        # Implement task storage
        pass
    
    def get_task(self, task_id):
        """Retrieve a task."""
        # Implement task retrieval
        pass
    
    def update_task_status(self, task_id, status):
        """Update task status."""
        # Implement status update
        pass
    
    def store_result(self, task_id, result):
        """Store a task result."""
        # Implement result storage
        pass
    
    def get_result(self, task_id):
        """Retrieve a task result."""
        # Implement result retrieval
        pass
    
    # Implement other required methods...

# Use custom backend
backend = CustomBackend({"option": "value"})
queue = sitq.TaskQueue(backend=backend)
```

## Backend Selection Guide

### Use SQLite When:
- Single-machine deployment
- Moderate throughput (< 1000 tasks/second)
- Need ACID compliance
- Want zero external dependencies
- Building prototypes or small applications

### Consider Custom Backend When:
- Need distributed deployment
- Require high throughput (> 1000 tasks/second)
- Have specific storage requirements
- Need integration with existing systems
- Require advanced features like sharding

## Performance Considerations

### SQLite Performance Tips

```python
# Optimize for high write throughput
backend = sitq.SQLiteBackend(
    database="write_heavy.db",
    enable_wal=True,          # Enable concurrent reads/writes
    synchronous="NORMAL",     # Less strict sync
    journal_mode="WAL",       # WAL mode
    cache_size=20000,         # Larger cache
    temp_store="MEMORY"       # Memory temp storage
)

# Optimize for read-heavy workloads
backend = sitq.SQLiteBackend(
    database="read_heavy.db",
    connection_pool_size=50,  # More connections for reads
    cache_size=50000,         # Much larger cache
    readonly=True             # Read-only if possible
)
```

### Monitoring Backend Performance

```python
# Monitor backend health
health = backend.health_check()
print(f"Backend healthy: {health.is_healthy}")
print(f"Database size: {health.database_size_mb} MB")
print(f"Active connections: {health.active_connections}")
print(f"Query performance: {health.avg_query_time} ms")

# Get backend statistics
stats = backend.get_stats()
print(f"Total tasks: {stats.total_tasks}")
print(f"Pending tasks: {stats.pending_tasks}")
print(f"Completed tasks: {stats.completed_tasks}")
print(f"Failed tasks: {stats.failed_tasks}")
```

## Backup and Recovery

### SQLite Backup

```python
# Create backup
backend.backup("backup_tasks.db")

# Restore from backup
backend.restore("backup_tasks.db")

# Scheduled backup
import schedule
import time

def backup_database():
    backend.backup(f"backup_{int(time.time())}.db")

# Backup every hour
schedule.every().hour.do(backup_database)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Data Migration

```python
# Migrate from one backend to another
old_backend = sitq.SQLiteBackend("old_tasks.db")
new_backend = sitq.SQLiteBackend("new_tasks.db")

# Migrate all tasks
task_ids = old_backend.list_all_tasks()
for task_id in task_ids:
    task = old_backend.get_task(task_id)
    new_backend.store_task(task)
    
    # Migrate result if exists
    if old_backend.has_result(task_id):
        result = old_backend.get_result(task_id)
        new_backend.store_result(task_id, result)
```

## Security Considerations

### Database Encryption

```python
# SQLite with encryption (requires sqlite3 extension)
backend = sitq.SQLiteBackend(
    database="encrypted.db",
    encryption_key="your-secret-key",
    cipher="AES-256"
)
```

### Access Control

```python
# Backend with access control
backend = sitq.SQLiteBackend(
    database="secure.db",
    read_only_users=["readonly_user"],
    write_users=["app_user"],
    admin_users=["admin_user"]
)
```

## Troubleshooting

### Common Issues

```python
# Database locked errors
backend = sitq.SQLiteBackend(
    database="tasks.db",
    connection_timeout=60.0,  # Increase timeout
    enable_wal=True          # Enable WAL mode
)

# Memory usage issues
backend = sitq.SQLiteBackend(
    database="tasks.db",
    cache_size=1000,          # Reduce cache size
    connection_pool_size=5    # Reduce pool size
)

# Performance issues
backend = sitq.SQLiteBackend(
    database="tasks.db",
    enable_wal=True,
    synchronous="OFF",       # Fastest but less safe
    journal_mode="MEMORY"     # In-memory journal
)
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

backend = sitq.SQLiteBackend(
    database="debug.db",
    debug=True,               # Enable debug mode
    log_queries=True          # Log all queries
)
```

## Best Practices

1. **Use WAL mode** for better concurrency
2. **Configure connection pooling** appropriately for your workload
3. **Monitor database size** and clean up old tasks
4. **Backup regularly** for data safety
5. **Use appropriate sync modes** for your safety/performance needs
6. **Test with realistic loads** before production deployment

## Next Steps

- [Task Queues Guide](task-queues.md) - Learn about queue management
- [Workers Guide](workers.md) - Explore task execution
- [Serialization Guide](serialization.md) - Understand data handling
- [Error Handling Guide](error-handling.md) - Comprehensive error management