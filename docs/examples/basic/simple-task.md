# Simple Task Processing

Learn the fundamental sitq workflow by creating a queue, enqueueing a task, and processing it with a worker.

## What You'll Learn

- How to set up a basic sitq TaskQueue
- How to define and enqueue async tasks
- How to process tasks with a Worker
- The basic lifecycle of a task (pending → in_progress → success)

## Prerequisites

- Basic understanding of Python async/await
- No prior task queue experience required

## Code Example

```python
import asyncio
from sitq import TaskQueue, Worker
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer

# Step 1: Define your async task function
# This is the work you want to be done in the background
async def say_hello():
    """A simple task that prints a greeting."""
    print("Hello from sitq!")
    return "Task completed successfully!"

async def main():
    # Step 2: Set up the task queue
    # The SQLiteBackend stores tasks in a local database file
    backend = SQLiteBackend("my_first_queue.db")
    # CloudpickleSerializer handles complex Python objects
    serializer = CloudpickleSerializer()

    # Use async context manager for proper setup and cleanup
    async with TaskQueue(backend, serializer) as queue:
        # Step 3: Enqueue your task
        # This creates a task and stores it in the database
        task_id = await queue.enqueue(say_hello)
        print(f"Task {task_id} enqueued!")

        # Step 4: Create and start a worker
        # The worker will pick up tasks and execute them
        worker = Worker(backend, serializer, max_concurrency=1)
        await worker.start()
        print("Worker started, processing tasks...")

        # Step 5: Wait for the task to complete
        await asyncio.sleep(2)  # Give worker time to process

        # Step 6: Stop the worker
        await worker.stop()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Concepts

### TaskQueue
The `TaskQueue` is your main interface for creating and managing tasks. It handles:
- Task serialization and persistence
- Task scheduling and queuing
- Result retrieval

### Worker
The `Worker` picks up pending tasks and executes them. Key features:
- **Concurrency**: Controls how many tasks run simultaneously
- **Lifecycle Management**: Start/stop workers as needed
- **Error Handling**: Automatically handles task failures

### Backend
Backends provide persistent storage for tasks. The `SQLiteBackend`:
- Uses a local SQLite database file
- Good for single-process applications
- Enables WAL mode for better concurrency

## Try It Yourself

1. Run the example and observe the output
2. Modify the `say_hello` function to do something different:
   ```python
   async def say_hello():
       print("Processing user data...")
       await asyncio.sleep(1)  # Simulate work
       return "User data processed!"
   ```
3. Add multiple enqueue calls to see how the worker handles several tasks

## Next Steps

- Learn about [Task Arguments](./task-arguments.md) to pass data to your tasks
- Explore [Multiple Workers](./multiple-workers.md) for parallel processing
- See [Advanced Examples](../../advanced/) for complex real-world patterns