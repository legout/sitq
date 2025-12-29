# Basic Concepts

Understanding the core concepts of sitq will help you build efficient and reliable task processing systems.

## Architecture Overview

sitq follows a simple but powerful architecture:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│ Task Queue  │◀───│   Worker    │
│             │    │             │───▶│             │
└─────────────┘    └─────────────┘    └─────────────┘
                           │
                           ▼
                   ┌─────────────┐
                   │   Backend   │
                   │  (Storage)  │
                   └─────────────┘
```

## Core Components

### 1. Tasks
Tasks are the fundamental unit of work in sitq. Each task contains:

- **Function**: The callable to execute
- **Arguments**: Positional and keyword arguments for the function
- **Metadata**: Task ID, timestamps, and status information

```python
# Tasks are enqueued directly with functions
task_id = await queue.enqueue(my_function, 1, 2, 3, option=True)
```

### 2. Task Queue
The task queue manages task lifecycle:

- **Enqueue**: Add new tasks to the queue
- **Dequeue**: Retrieve tasks for processing
- **Status Tracking**: Monitor task progress
- **Result Storage**: Store task results

```python
from sitq import TaskQueue, SQLiteBackend

queue = TaskQueue(backend=SQLiteBackend("tasks.db"))
task_id = await queue.enqueue(my_function, 1, 2, 3, option=True)
```

### 3. Workers
Workers execute tasks from the queue:

- **Task Processing**: Execute tasks and handle results
- **Error Handling**: Capture and report task failures
- **Concurrent Processing**: Handle multiple tasks simultaneously

```python
worker = sitq.Worker(queue)
result = worker.process_task(task_id)
```

### 4. Backends
Backends provide persistent storage:

- **Task Storage**: Save tasks between restarts
- **Result Storage**: Store task results
- **State Management**: Track queue and worker state

```python
backend = sitq.SQLiteBackend("tasks.db")
```

## Task Lifecycle

```
┌─────────┐   Enqueue   ┌──────────┐   Dequeue   ┌──────────┐
│ Created │────────────▶│ Queued  │────────────▶│Running   │
└─────────┘             └──────────┘             └──────────┘
                                                   │
                                            Success │ Failure
                                                   ▼
                                           ┌─────────────┐
                                           │ Completed   │
                                           └─────────────┘
```

## Key Features

### Serialization
sitq automatically serializes tasks and results:

```python
# Functions and arguments are serialized for storage
task = sitq.Task(function=my_function, args=[data])
task_id = queue.enqueue(task)

# Results are serialized when stored
result = worker.process_task(task_id)
```

### Error Handling
Robust error handling at every level:

```python
try:
    result = worker.process_task(task_id)
    if result.is_error:
        print(f"Task failed: {result.error}")
    else:
        print(f"Task succeeded: {result.value}")
except sitq.TaskNotFoundError:
    print("Task not found")
except sitq.WorkerError as e:
    print(f"Worker error: {e}")
```

### Synchronous Wrapper
For simple use cases, use the sync wrapper:

```python
with sitq.SyncTaskQueue() as queue:
    task_id = queue.enqueue(my_task)
    result = queue.get_result(task_id)
```

## Design Principles

### Simplicity
- Minimal API surface
- Intuitive naming conventions
- Clear separation of concerns

### Reliability
- Persistent task storage
- Comprehensive error handling
- Graceful failure recovery

### Performance
- Efficient serialization
- Concurrent task processing
- Minimal overhead

### Flexibility
- Pluggable backends
- Configurable workers
- Extensible architecture

## When to Use sitq

sitq is ideal for:

- **Background Processing**: Run tasks asynchronously
- **Batch Jobs**: Process large datasets in chunks
- **Microservices**: Coordinate distributed work
- **Web Applications**: Handle long-running requests
- **Data Pipelines**: Process data through multiple stages

## When Not to Use sitq

Consider alternatives for:

- **Real-time Processing**: Use streaming frameworks
- **Complex Workflows**: Use workflow engines
- **Distributed Computing**: Use distributed task queues
- **Simple Scripts**: Direct function calls may be sufficient

## Next Steps

- [Installation](../how-to/installation.md) - Set up sitq
- [Quickstart](quickstart.md) - Try a basic example
- [How-to Guides](../how-to/) - Explore advanced features
- [API Reference](../reference/api/) - Detailed API documentation