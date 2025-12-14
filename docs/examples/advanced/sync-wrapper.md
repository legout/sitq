# Using the Synchronous Wrapper

For non-`async` applications, you can use the `SyncTaskQueue` wrapper for easy integration into legacy codebases.

## Code Example

**`sync_example.py`**
```python
from sitq import SyncTaskQueue, Result
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer

def add(x, y):
    """Simple synchronous task function."""
    return x + y

def process_data(data_list):
    """Process a list of data synchronously."""
    processed = []
    for item in data_list:
        # Simulate some processing
        processed.append({
            "id": item["id"],
            "name": item["name"].upper(),
            "processed": True
        })
    return processed

def file_operations(filename):
    """Synchronous file operation task."""
    import os
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            content = f.read()
        return {
            "filename": filename,
            "size": len(content),
            "lines": len(content.splitlines())
        }
    else:
        raise FileNotFoundError(f"File {filename} not found")

# The SyncTaskQueue manages the event loop internally
def main():
    """Main synchronous function using SyncTaskQueue."""
    print("=== SyncTaskQueue Example ===\n")

    # Set up the synchronous task queue
    backend = SQLiteBackend("sync_queue.db")
    serializer = CloudpickleSerializer()

    # Use context manager for automatic cleanup
    with SyncTaskQueue(
        backend=backend,
        serializer=serializer
    ) as queue:

        print("1. Basic task enqueuing:")
        # Enqueue simple tasks
        task_id1 = queue.enqueue(add, 5, 10)
        task_id2 = queue.enqueue(add, 20, 30)
        print(f"Enqueued task 1: {task_id1}")
        print(f"Enqueued task 2: {task_id2}")

        print("\n2. Getting results:")
        # Get results (these will be None until workers process the tasks)
        result1 = queue.get_result(task_id1, timeout=1)
        result2 = queue.get_result(task_id2, timeout=1)

        print(f"Result 1: {result1}")
        print(f"Result 2: {result2}")

        print("\n3. Processing complex data:")
        # Enqueue more complex tasks
        sample_data = [
            {"id": 1, "name": "alice"},
            {"id": 2, "name": "bob"},
            {"id": 3, "name": "charlie"}
        ]

        task_id3 = queue.enqueue(process_data, sample_data)
        print(f"Enqueued data processing task: {task_id3}")

        # Create some test files first
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Line 1\nLine 2\nLine 3\n")
            temp_filename = f.name

        task_id4 = queue.enqueue(file_operations, temp_filename)
        print(f"Enqueued file operation task: {task_id4}")

        print("\n4. Batch processing:")
        # Enqueue multiple tasks
        batch_tasks = []
        for i in range(5):
            task_id = queue.enqueue(add, i * 10, i * 20)
            batch_tasks.append(task_id)

        print(f"Enqueued {len(batch_tasks)} batch tasks")

        # Note: You still need to run an async worker separately
        # to process the tasks from the queue.
        print("\n⚠️  Note: Workers need to be started separately!")
        print("   In production, you'd run workers in separate processes/threads.")

def worker_process_example():
    """Example of how to run workers for sync tasks."""
    import asyncio

    async def run_workers():
        """Run workers to process sync queue tasks."""
        backend = SQLiteBackend("sync_queue.db")
        serializer = CloudpickleSerializer()

        # Start workers to process the tasks
        from sitq import Worker
        worker = Worker(backend, serializer, concurrency=2)

        print("Starting workers...")
        await worker.start()

        # Run workers for a while
        await asyncio.sleep(5)

        print("Stopping workers...")
        await worker.stop()
        await backend.close()

    # Run the workers
    asyncio.run(run_workers())

if __name__ == "__main__":
    # Run the main sync example
    main()

    print("\n" + "="*50)
    print("To process the tasks, run workers in another process:")
    print("python -c \"from sync_example import worker_process_example; worker_process_example()\"")
```