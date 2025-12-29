# SQLite Backend

Configure and use the SQLite backend for task persistence.

## Overview

[`SQLiteBackend`](../reference/api/sitq.backends.sqlite.md) provides SQLite-based storage for tasks and results. It's the default and recommended backend for most use cases.

## Basic Setup

### In-Memory Database

For testing and development:

```python
from sitq import SQLiteBackend

# In-memory SQLite (data lost when process exits)
backend = SQLiteBackend(":memory:")
```

### File-Based Database

For production and persistence:

```python
# File-based SQLite (persists across restarts)
backend = SQLiteBackend("tasks.db")

# With absolute path
backend = SQLiteBackend("/full/path/to/tasks.db")

# With Path object
from pathlib import Path
backend = SQLiteBackend(Path.cwd() / "data" / "tasks.db")
```

## Connecting to Queue

Use backend with [`TaskQueue`](../reference/api/sitq.queue.md):

```python
from sitq import TaskQueue, SQLiteBackend, Worker

backend = SQLiteBackend("tasks.db")
queue = TaskQueue(backend=backend)

# Use queue to enqueue tasks
task_id = await queue.enqueue(my_function, "arg")

# Use backend with worker
worker = Worker(backend)
```

## Database Schema

SQLite backend automatically creates tables:

- `tasks` - Store task definitions
- `results` - Store task results

Tables are created on first use.

## Connection Management

### Connection Pooling

Backend manages connections automatically:

```python
# Backend handles connections internally
backend = SQLiteBackend("tasks.db")

# Multiple queue instances can share the same backend
queue1 = TaskQueue(backend=backend)
queue2 = TaskQueue(backend=backend)
```

### Async Context Manager

Use with async context for cleanup:

```python
async def main():
    async with backend:
        # Create queue
        queue = TaskQueue(backend=backend)
        
        # Enqueue and process tasks
        task_id = await queue.enqueue(my_function, "arg")
        
        worker = Worker(backend)
        await worker.start()
        await asyncio.sleep(1)
        await worker.stop()

asyncio.run(main())
```

## Performance Tuning

### Database Optimization

```python
import sqlite3

# Connect to database for manual optimization
conn = sqlite3.connect("tasks.db")

# Enable WAL mode for better concurrency
conn.execute("PRAGMA journal_mode=WAL")

# Set appropriate cache size
conn.execute("PRAGMA cache_size=-64000")  # 64MB cache

# Increase timeout for busy databases
conn.execute("PRAGMA busy_timeout=5000")  # 5 seconds

conn.close()
```

### Vacuum Database

Reclaim space from deleted records:

```python
import sqlite3

conn = sqlite3.connect("tasks.db")
conn.execute("VACUUM")
conn.close()
```

## Common Operations

### Checking Database Size

```python
import os

db_path = "tasks.db"
size_bytes = os.path.getsize(db_path)
size_mb = size_bytes / (1024 * 1024)
print(f"Database size: {size_mb:.2f} MB")
```

### Backing Up Database

```python
import shutil
from datetime import datetime

backup_path = f"tasks_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
shutil.copy2("tasks.db", backup_path)
print(f"Backup created: {backup_path}")
```

### Migrating Database

```python
import shutil

# Stop all workers and queues first
# Then create backup and migrate
backup = f"tasks_backup.db"
shutil.copy2("tasks.db", backup)

# New database
new_backend = SQLiteBackend("tasks_new.db")
queue = TaskQueue(backend=new_backend)

# Test new backend, then switch
# shutil.move("tasks_new.db", "tasks.db")
```

## Troubleshooting

### Database Locked

Error: `sqlite3.OperationalError: database is locked`

```python
# Solution 1: Use WAL mode
import sqlite3
conn = sqlite3.connect("tasks.db")
conn.execute("PRAGMA journal_mode=WAL")
conn.close()

# Solution 2: Ensure single writer
# Don't use multiple backends writing to same file concurrently
# Use separate databases for high concurrency
```

### Database Corruption

Error: `sqlite3.DatabaseError: database disk image is malformed`

```python
# Try to recover
import sqlite3

# Create new database
new_conn = sqlite3.connect("tasks_new.db")

# Try to dump from old database
old_conn = sqlite3.connect("tasks.db")
for line in old_conn.iterdump():
    new_conn.execute(line)

# Close connections
old_conn.close()
new_conn.close()

# Replace old with new
import shutil
shutil.move("tasks_new.db", "tasks.db")
```

### Slow Performance

```python
# Enable indexing
import sqlite3

conn = sqlite3.connect("tasks.db")
conn.execute("ANALYZE")
conn.close()

# Increase cache size (see Performance Tuning above)
# Or use in-memory backend for testing
```

## Best Practices

1. **Use WAL mode** for better concurrency
2. **Back up regularly** to prevent data loss
3. **Monitor database size** and vacuum periodically
4. **Use absolute paths** for file-based databases
5. **Close connections** properly with context managers
6. **Test with in-memory** before using file-based

## When to Use SQLite Backend

### Good For:

- Single-machine deployments
- Small to medium task volumes (<10,000 tasks/day)
- Development and testing
- Applications without existing database infrastructure

### Consider Alternatives For:

- High-concurrency multi-worker deployments
- Very high task volumes (>10,000 tasks/day)
- Distributed systems
- Applications with existing PostgreSQL/Redis infrastructure

## What's Next?

- [Running Workers](run-worker.md) - Worker configuration
- [Task Queues](task-queues.md) - Queue management
- [Backend Reference](../reference/api/sitq.backends.sqlite.md) - API documentation

## See Also

- [`SQLiteBackend`](../reference/api/sitq.backends.sqlite.md) - Backend API reference
- [`Backend`](../reference/api/sitq.backends.base.md) - Backend base class
- [Architecture](../explanation/architecture.md) - Backend design
