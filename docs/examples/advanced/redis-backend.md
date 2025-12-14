# Using the Redis Backend

This example shows how to use the Redis backend for distributed task queue operations.

## Code Example

```python
import asyncio
from sitq import TaskQueue, Worker
from sitq.backends.redis import RedisBackend  # When available
from sitq.serialization import CloudpickleSerializer

# Define your task functions
async def process_user_data(user_id: int, data: dict):
    """Process user data with Redis backend."""
    # Simulate data processing
    await asyncio.sleep(0.5)
    processed_data = {
        "user_id": user_id,
        "original_data": data,
        "processed_at": "2024-01-01T12:00:00Z",
        "status": "processed"
    }
    return processed_data

async def main():
    # Use RedisBackend for distributed task processing
    # This enables multiple processes/machines to share the same queue
    backend = RedisBackend(
        host="localhost",
        port=6379,
        db=0,
        password=None  # Add password if needed
    )
    serializer = CloudpickleSerializer()
    queue = TaskQueue(backend, serializer)

    # Connect to Redis
    await queue.connect()

    # Enqueue multiple tasks
    user_data = [
        (1, {"name": "Alice", "email": "alice@example.com"}),
        (2, {"name": "Bob", "email": "bob@example.com"}),
        (3, {"name": "Charlie", "email": "charlie@example.com"}),
    ]

    task_ids = []
    for user_id, data in user_data:
        task_id = await queue.enqueue(process_user_data, user_id, data)
        task_ids.append(task_id)
        print(f"Enqueued task for user {user_id}: {task_id}")

    # Start worker to process tasks
    worker = Worker(backend, serializer, concurrency=3)
    await worker.start()

    # Wait for tasks to complete
    await asyncio.sleep(3)

    # Collect results
    results = []
    for task_id in task_ids:
        result = await queue.get_result(task_id, timeout=5)
        if result and result.is_success():
            results.append(result.value)

    print(f"Processed {len(results)} users successfully")

    # Cleanup
    await worker.stop()
    await queue.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Features

- **Distributed Processing**: Multiple workers can process tasks from the same queue
- **Persistent Storage**: Tasks survive worker restarts
- **Network Access**: Workers can run on different machines
- **High Availability**: Redis provides built-in replication options

## Requirements

- Redis server running and accessible
- Redis Python client library (`redis-py`)
- Network connectivity between all workers and Redis

## Configuration Options

```python
# Basic connection
RedisBackend(host="localhost", port=6379)

# With authentication
RedisBackend(host="localhost", port=6379, password="your_password")

# With connection pooling
RedisBackend(
    host="localhost", 
    port=6379,
    max_connections=20,
    connection_timeout=5,
    health_check_interval=30
)
```