# Task with Arguments

Learn how to pass data to your tasks using positional and keyword arguments, and work with different data types.

## What You'll Learn

- How to pass arguments to task functions
- Working with different data types (strings, numbers, lists, dicts)
- Using keyword arguments for flexible task configuration
- Return values from tasks

## Prerequisites

- Complete [Simple Task Processing](./simple-task.md) first
- Understanding of Python function arguments

## Code Example

```python
import asyncio
from sitq import TaskQueue, Worker
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer

# Step 1: Define tasks that accept arguments
async def greet_user(name: str, age: int = 25):
    """Greet a user with their name and age."""
    message = f"Hello, {name}! You are {age} years old."
    print(message)
    return message

async def process_data(data: list, multiplier: int = 1):
    """Process a list of numbers with a multiplier."""
    if not data:
        return []

    result = [x * multiplier for x in data]
    print(f"Processing {data} with multiplier {multiplier}: {result}")
    return result

async def format_report(title: str, content: dict, include_timestamp: bool = True):
    """Create a formatted report with optional timestamp."""
    report_lines = [f"# {title}", ""]

    if include_timestamp:
        from datetime import datetime
        report_lines.append(f"Generated: {datetime.now().isoformat()}")
        report_lines.append("")

    for key, value in content.items():
        report_lines.append(f"- {key}: {value}")

    report = "\n".join(report_lines)
    print("Report created:")
    print(report)
    return report

async def main():
    # Set up the queue
    backend = SQLiteBackend("arguments_queue.db")
    serializer = CloudpickleSerializer()

    async with TaskQueue(backend, serializer) as queue:
        # Create and start worker
        worker = Worker(backend, serializer, max_concurrency=2)
        await worker.start()

    print("=== Demonstrating Task Arguments ===\n")

    # Example 1: Positional arguments
    print("1. Positional arguments:")
    task_id1 = await queue.enqueue(greet_user, "Alice", 30)
    print(f"Enqueued task {task_id1}")

    # Example 2: Keyword arguments
    print("\n2. Keyword arguments:")
    task_id2 = await queue.enqueue(greet_user, name="Bob", age=25)
    print(f"Enqueued task {task_id2}")

    # Example 3: Mixed arguments
    print("\n3. Mixed positional and keyword arguments:")
    task_id3 = await queue.enqueue(greet_user, "Charlie", age=35)
    print(f"Enqueued task {task_id3}")

    # Example 4: Complex data structures
    print("\n4. Complex data structures:")
    test_data = [1, 2, 3, 4, 5]
    task_id4 = await queue.enqueue(process_data, test_data, multiplier=3)
    print(f"Enqueued task {task_id4}")

    # Example 5: Dictionary and multiple keyword arguments
    print("\n5. Dictionary and keyword arguments:")
    report_content = {
        "total_users": 150,
        "active_sessions": 23,
        "error_rate": 0.02
    }
    task_id5 = await queue.enqueue(
        format_report,
        title="System Status Report",
        content=report_content,
        include_timestamp=True
    )
    print(f"Enqueued task {task_id5}")

        # Wait for processing
        await asyncio.sleep(3)

        # Stop worker and cleanup
        await worker.stop()
        print("\n=== All tasks completed ===")

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Concepts

### Argument Types
sitq supports all Python argument patterns:

- **Positional Arguments**: `await queue.enqueue(task_func, arg1, arg2)`
- **Keyword Arguments**: `await queue.enqueue(task_func, key1=value1, key2=value2)`
- **Mixed Arguments**: `await queue.enqueue(task_func, arg1, key2=value2)`

### Data Serialization
The `CloudpickleSerializer` can handle:
- Basic types (str, int, float, bool)
- Collections (list, dict, tuple, set)
- Custom objects and classes
- Functions and lambdas

### Return Values
Tasks can return any serializable value:
- Results are stored in the backend
- Retrieve with `queue.get_result(task_id)`
- See [Task Results](./task-results.md) for details

## Try It Yourself

1. Create a task that accepts a dictionary and returns statistics:
   ```python
   async def calculate_stats(numbers: list):
       if not numbers:
           return {"count": 0, "sum": 0, "average": 0}
       return {
           "count": len(numbers),
           "sum": sum(numbers),
           "average": sum(numbers) / len(numbers)
       }
   ```

2. Experiment with different data types:
   - Try passing a custom class instance
   - Use nested dictionaries and lists
   - Test with None values and empty collections

3. Modify the examples to use your own data and see how it works

## Next Steps

- Learn about [Multiple Workers](./multiple-workers.md) to process tasks in parallel
- Explore [Task Results](./task-results.md) to retrieve and use task outputs
- See [Batch Processing](./batch-processing.md) for efficient bulk operations