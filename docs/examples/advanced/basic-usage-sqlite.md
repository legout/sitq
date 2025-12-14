# Basic Usage with SQLite Backend

This example demonstrates the fundamental sitq workflow using the SQLite backend for persistent task storage.

## Code Example

**`main.py`**
```python
import asyncio
from sitq import TaskQueue, Worker, Result
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer

# 1. Define your async task function
async def say_hello(name: str):
    print(f"Hello, {name}")
    return f"Greetings, {name}!"

async def main():
    # 2. Set up the queue with a backend and serializer
    backend = SQLiteBackend("example_queue.db")
    serializer = CloudpickleSerializer()
    queue = TaskQueue(backend, serializer)

    # 3. Enqueue a task and get its ID
    task_id = await queue.enqueue(say_hello, "World")
    print(f"Task {task_id} enqueued.")

    # 4. Start a worker to process the task
    worker = Worker(backend, serializer, concurrency=5)

    # Run the worker for a short period to process the task
    await worker.start()
    await asyncio.sleep(1) # Allow time for the task to be processed
    await worker.stop()

    # 5. Retrieve the result
    result = await queue.get_result(task_id, timeout=5)
    if result and result.is_success():
        print(f"Result received: {result.status}")
        print(f"Task return value: {result.value}")
    else:
        print("Did not receive result in time.")

    # 6. Clean up
    await queue.close()

if __name__ == "__main__":
    asyncio.run(main())
```

**To run this:**
1. Save the code as `main.py`.
2. Run `python main.py` from your terminal.

**Expected Output:**
```
Task <uuid> enqueued.
Hello, World
Result received: success
Task return value: Greetings, World!
```