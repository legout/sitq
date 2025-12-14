# Sync vs Async

Learn the differences between sitq's synchronous and asynchronous APIs, and understand when to use each approach.

## What You'll Learn

- Difference between async and sync task queue APIs
- When to use TaskQueue vs SyncTaskQueue
- Performance implications of each approach
- Migrating from sync to async code

## Prerequisites

- Understanding of Python async/await concepts
- Basic familiarity with task queues

## Code Example

```python
import asyncio
import time
from typing import List, Any
from sitq import TaskQueue, Worker, Result, SyncTaskQueue
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer

# Step 1: Define both sync and async task functions
async def async_calculation(numbers: List[int]) -> int:
    """Async task for CPU-intensive calculation."""
    await asyncio.sleep(0.1)  # Simulate async work
    result = sum(n * n for n in numbers)
    print(f"Async calculation completed: {result}")
    return result

def sync_calculation(numbers: List[int]) -> int:
    """Sync task for CPU-intensive calculation."""
    time.sleep(0.1)  # Simulate sync work (blocking)
    result = sum(n * n for n in numbers)
    print(f"Sync calculation completed: {result}")
    return result

async def async_io_task(url: str) -> str:
    """Async task simulating I/O operation."""
    await asyncio.sleep(0.2)  # Simulate network request
    return f"Fetched data from {url}"

def sync_io_task(url: str) -> str:
    """Sync task simulating I/O operation."""
    time.sleep(0.2)  # Simulate blocking I/O
    return f"Fetched data from {url}"

# Step 2: Async TaskQueue Example
async def demonstrate_async_queue():
    """Show how to use the async TaskQueue API."""
    print("🔄 Async TaskQueue Example:")
    print("=" * 40)

    # Set up async queue
    backend = SQLiteBackend("async_queue.db")
    serializer = CloudpickleSerializer()
    queue = TaskQueue(backend, serializer)
    await queue.connect()

    # Create async worker
    worker = Worker(backend, serializer, concurrency=3)
    await worker.start()

    # Enqueue multiple async tasks
    task_ids = []
    for i in range(5):
        task_id = await queue.enqueue(async_calculation, list(range(i * 10, (i + 1) * 10)))
        task_ids.append(task_id)
        print(f"📤 Enqueued async task {i}: {task_id[:8]}...")

    # Wait for all tasks to complete
    start_time = time.time()
    results = {}

    for task_id in task_ids:
        result = await queue.get_result(task_id, timeout=10)
        results[task_id] = result

    duration = time.time() - start_time

    # Process results
    successful_results = []
    for task_id, result in results.items():
        if result and result.is_success():
            successful_results.append(result.value)

    print(f"✅ Async processing completed in {duration:.2f}s")
    print(f"   Processed {len(successful_results)} tasks")
    print(f"   Results: {successful_results[:3]}...")  # Show first 3

    # Cleanup
    await worker.stop()
    await queue.close()
    return duration, len(successful_results)

# Step 3: Sync TaskQueue Example
def demonstrate_sync_queue():
    """Show how to use the sync TaskQueue API."""
    print("\n🔄 Sync TaskQueue Example:")
    print("=" * 40)

    # Set up sync queue
    backend = SQLiteBackend("sync_queue.db")
    serializer = CloudpickleSerializer()

    # Use context manager for automatic cleanup
    with SyncTaskQueue(backend, serializer) as queue:
        # Enqueue multiple sync tasks
        task_ids = []
        for i in range(5):
            task_id = queue.enqueue(sync_calculation, list(range(i * 10, (i + 1) * 10)))
            task_ids.append(task_id)
            print(f"📤 Enqueued sync task {i}: {task_id[:8]}...")

        # Note: You still need to run workers separately
        # This is shown in the main function

        return task_ids

# Step 4: Performance Comparison
async def performance_comparison():
    """Compare performance between async and sync approaches."""
    print("\n📊 Performance Comparison:")
    print("=" * 50)

    # Test 1: Async I/O tasks
    print("\n1. Testing async I/O tasks:")

    backend = SQLiteBackend("perf_async.db")
    serializer = CloudpickleSerializer()
    async_queue = TaskQueue(backend, serializer)
    await async_queue.connect()

    async_worker = Worker(backend, serializer, concurrency=5)
    await async_worker.start()

    start_time = time.time()
    async_task_ids = []
    for i in range(10):
        task_id = await async_queue.enqueue(async_io_task, f"https://api.example.com/data/{i}")
        async_task_ids.append(task_id)

    # Wait for completion
    async_results = []
    for task_id in async_task_ids:
        result = await async_queue.get_result(task_id, timeout=5)
        if result and result.is_success():
            async_results.append(result.value)

    async_duration = time.time() - start_time

    await async_worker.stop()
    await async_queue.close()

    print(f"   Async I/O: {async_duration:.2f}s for {len(async_results)} tasks")

    # Test 2: Sync I/O tasks (using multiple workers)
    print("\n2. Testing sync I/O tasks:")

    backend2 = SQLiteBackend("perf_sync.db")
    sync_queue = SyncTaskQueue(backend2, serializer)

    sync_task_ids = []
    with sync_queue:
        for i in range(10):
            task_id = sync_queue.enqueue(sync_io_task, f"https://api.example.com/data/{i+10}")
            sync_task_ids.append(task_id)

    # Start sync workers (you'd run these in separate processes/threads in production)
    # For demo, we'll run a single worker
    sync_worker = Worker(backend2, serializer, concurrency=2)
    await sync_worker.start()

    start_time = time.time()
    sync_results = []
    for task_id in sync_task_ids:
        result = await sync_queue.get_result(task_id, timeout=5)
        if result and result.is_success():
            sync_results.append(result.value)

    sync_duration = time.time() - start_time

    await sync_worker.stop()

    print(f"   Sync I/O: {sync_duration:.2f}s for {len(sync_results)} tasks")

    # Results
    print(f"\n📈 Performance Summary:")
    print(f"   Async: {async_duration:.2f}s")
    print(f"   Sync:  {sync_duration:.2f}s")
    if sync_duration > 0:
        speedup = sync_duration / async_duration
        print(f"   Speedup: {speedup:.2f}x")

# Step 5: Migration Guide
def migration_guide():
    """Show how to migrate from sync to async."""
    print("\n🔄 Migration Guide:")
    print("=" * 50)

    print("\n📋 Before (Sync API):")
    print("```python")
    print("from sitq import SyncTaskQueue")
    print("from sitq.backends.sqlite import SQLiteBackend")
    print("from sitq.serialization import CloudpickleSerializer")
    print("")
    print("backend = SQLiteBackend('tasks.db')")
    print("serializer = CloudpickleSerializer()")
    print("")
    print("with SyncTaskQueue(backend, serializer) as queue:")
    print("    task_id = queue.enqueue(my_function, arg1, arg2)")
    print("    result = queue.get_result(task_id)")
    print("```")

    print("\n📋 After (Async API):")
    print("```python")
    print("import asyncio")
    print("from sitq import TaskQueue, Worker")
    print("from sitq.backends.sqlite import SQLiteBackend")
    print("from sitq.serialization import CloudpickleSerializer")
    print("")
    print("async def main():")
    print("    backend = SQLiteBackend('tasks.db')")
    print("    serializer = CloudpickleSerializer()")
    print("    queue = TaskQueue(backend, serializer)")
    print("    await queue.connect()")
    print("")
    print("    worker = Worker(backend, serializer)")
    print("    await worker.start()")
    print("")
    print("    task_id = await queue.enqueue(my_function, arg1, arg2)")
    print("    result = await queue.get_result(task_id)")
    print("")
    print("    await worker.stop()")
    print("    await queue.close()")
    print("")
    print("asyncio.run(main())")
    print("```")

# Step 6: Use Case Examples
async def use_case_examples():
    """Show specific use cases for sync vs async."""
    print("\n🎯 Use Case Examples:")
    print("=" * 50)

    print("\n✅ Use Async TaskQueue when:")
    print("   • Building web applications (FastAPI, Flask with async)")
    print("   • Processing I/O-bound tasks (API calls, database queries)")
    print("   • Need high concurrency for many small tasks")
    print("   • Building real-time applications")
    print("   • Working with async frameworks")

    print("\n✅ Use Sync TaskQueue when:")
    print("   • Integrating with existing sync codebases")
    print("   • Building CLI tools or scripts")
    print("   • Processing CPU-bound tasks with ProcessWorker")
    print("   • Migrating gradually from sync to async")
    print("   • Using frameworks without async support")

    # Demonstrate hybrid approach
    print("\n🔄 Hybrid Approach (Recommended):")
    print("   • Use SyncTaskQueue for task creation")
    print("   • Use Async workers for task processing")
    print("   • This combines the best of both worlds")

# Step 7: Main demonstration
async def main():
    """Run all sync vs async demonstrations."""
    print("=== Sync vs Async TaskQueue Example ===\n")

    # Async example
    async_duration, async_count = await demonstrate_async_queue()

    # Sync example (note: workers need to be started separately)
    print("\n🔄 Starting sync worker for sync tasks...")
    sync_backend = SQLiteBackend("sync_queue.db")
    sync_serializer = CloudpickleSerializer()
    sync_worker = Worker(sync_backend, sync_serializer, concurrency=2)
    await sync_worker.start()

    # The sync tasks were enqueued in demonstrate_sync_queue()
    # but we need to wait for them to complete
    await asyncio.sleep(3)  # Wait for sync tasks to complete

    await sync_worker.stop()

    # Performance comparison
    await performance_comparison()

    # Migration guide
    migration_guide()

    # Use cases
    await use_case_examples()

    print("\n✅ Sync vs Async example completed!")

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Concepts

### Async TaskQueue
- **Full Async Support**: All operations are non-blocking
- **High Concurrency**: Can handle many tasks simultaneously
- **Event Loop**: Requires async context (asyncio.run())
- **Best For**: I/O-bound tasks, web applications, real-time systems

### Sync TaskQueue
- **Blocking Operations**: Traditional synchronous API
- **Easy Integration**: Works with existing sync code
- **Context Manager**: Automatic cleanup with `with` statement
- **Best For**: CLI tools, existing codebases, gradual migration

### Performance Considerations

**Async Advantages:**
- Better throughput for I/O-bound tasks
- Lower memory usage for many concurrent tasks
- Non-blocking operations allow better resource utilization

**Sync Advantages:**
- Simpler mental model for developers
- Better for CPU-bound tasks (can use ProcessWorker)
- Easier debugging and testing

## Decision Matrix

| Scenario | Recommended API | Reason |
|----------|-----------------|---------|
| Web application | Async | Non-blocking I/O, high concurrency |
| CLI tool | Sync | Simpler integration |
| CPU-intensive work | Sync + ProcessWorker | Better for CPU-bound tasks |
| Gradual migration | Start Sync, move to Async | Incremental adoption |
| High-frequency API | Async | Better performance under load |
| Legacy codebase | Sync | Minimal code changes required |

## Try It Yourself

1. **Convert a sync script to async:**
   - Start with SyncTaskQueue
   - Identify I/O-bound operations
   - Gradually migrate to async/await

2. **Test performance:**
   - Run identical workloads with both APIs
   - Measure throughput and latency
   - Profile resource usage

3. **Create a hybrid solution:**
   - Use SyncTaskQueue for task creation
   - Use Async workers for processing
   - This provides flexibility

## Best Practices

### For Async TaskQueue
```python
# Always use context managers or proper cleanup
async with TaskQueue(backend, serializer) as queue:
    task_id = await queue.enqueue(task_function, arg)
    result = await queue.get_result(task_id)

# Or explicit cleanup
queue = TaskQueue(backend, serializer)
await queue.connect()
try:
    task_id = await queue.enqueue(task_function, arg)
    result = await queue.get_result(task_id)
finally:
    await queue.close()
```

### For Sync TaskQueue
```python
# Use context managers for automatic cleanup
with SyncTaskQueue(backend, serializer) as queue:
    task_id = queue.enqueue(task_function, arg)
    result = queue.get_result(task_id)
```

## Next Steps

- Explore [Advanced Examples](../../advanced/) for production patterns
- Review [Error Handling](./error-handling.md) for robust error management
- Check out [Multiple Workers](./multiple-workers.md) for scaling strategies