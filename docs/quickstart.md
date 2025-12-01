# Quickstart

Get started with sitq in just a few minutes. This guide will walk you through creating your first task queue and processing tasks.

## Basic Example

```python
import sitq
import time

# 1. Create a task queue with SQLite backend
queue = sitq.TaskQueue(backend=sitq.SQLiteBackend(":memory:"))

# 2. Define a simple task function
def process_data(data):
    """Process some data and return the result."""
    time.sleep(0.1)  # Simulate work
    return f"Processed: {data}"

# 3. Enqueue some tasks
task_ids = []
for i in range(5):
    task = sitq.Task(
        function=process_data,
        args=[f"data_{i}"]
    )
    task_id = queue.enqueue(task)
    task_ids.append(task_id)
    print(f"Enqueued task: {task_id}")

# 4. Create a worker to process tasks
worker = sitq.Worker(queue)

# 5. Process tasks
print("\nProcessing tasks:")
for task_id in task_ids:
    result = worker.process_task(task_id)
    print(f"Task {task_id}: {result.value}")
```

## Running the Example

Save the code above as `quickstart_example.py` and run:

```bash
python quickstart_example.py
```

Expected output:
```
Enqueued task: 1
Enqueued task: 2
Enqueued task: 3
Enqueued task: 4
Enqueued task: 5

Processing tasks:
Task 1: Processed: data_0
Task 2: Processed: data_1
Task 3: Processed: data_2
Task 4: Processed: data_3
Task 5: Processed: data_4
```

## Key Concepts

### Tasks
Tasks are units of work that can be executed asynchronously:

```python
task = sitq.Task(
    function=my_function,      # Function to execute
    args=[arg1, arg2],         # Positional arguments
    kwargs={"key": "value"}    # Keyword arguments
)
```

### Backends
Backends provide storage for tasks and results:

```python
# In-memory SQLite (for testing)
backend = sitq.SQLiteBackend(":memory:")

# File-based SQLite (for persistence)
backend = sitq.SQLiteBackend("tasks.db")
```

### Workers
Workers execute tasks from the queue:

```python
worker = sitq.Worker(queue)

# Process a single task
result = worker.process_task(task_id)

# Process tasks continuously
worker.run()
```

## Next Steps

- [Basic Concepts](basic-concepts.md) - Learn about the architecture
- [Task Queues](../user-guide/task-queues.md) - Deep dive into queue management
- [Workers](../user-guide/workers.md) - Advanced worker configuration
- [Examples](../user-guide/examples/) - Real-world usage patterns

## Troubleshooting

**Import Error**: Make sure sitq is installed:
```bash
pip install sitq
```

**Database Error**: Check that the SQLite backend path is accessible:
```python
# Use absolute path for file-based storage
backend = sitq.SQLiteBackend("/full/path/to/tasks.db")
```

**Task Fails**: Check the result for errors:
```python
result = worker.process_task(task_id)
if result.is_error:
    print(f"Task failed: {result.error}")
else:
    print(f"Task succeeded: {result.value}")
```