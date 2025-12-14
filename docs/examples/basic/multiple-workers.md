# Multiple Workers

Learn how to use multiple workers to process tasks in parallel for better performance and throughput.

## What You'll Learn

- How to create and manage multiple Worker instances
- Understanding worker concurrency and parallelism
- Coordinating multiple workers for higher throughput
- Worker lifecycle management with multiple instances

## Prerequisites

- Complete [Task Arguments](./task-arguments.md) first
- Basic understanding of concurrent programming concepts

## Code Example

```python
import asyncio
import time
from sitq import TaskQueue, Worker
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer

# Step 1: Define tasks with varying execution times
async def quick_task(task_id: int):
    """A quick task that takes minimal time."""
    await asyncio.sleep(0.1)  # Simulate minimal work
    print(f"Quick task {task_id} completed")
    return f"Quick result {task_id}"

async def medium_task(task_id: int):
    """A medium task that takes moderate time."""
    await asyncio.sleep(0.5)  # Simulate moderate work
    print(f"Medium task {task_id} completed")
    return f"Medium result {task_id}"

async def slow_task(task_id: int):
    """A slow task that takes longer to complete."""
    await asyncio.sleep(1.0)  # Simulate longer work
    print(f"Slow task {task_id} completed")
    return f"Slow result {task_id}"

async def worker_info(worker_id: str, task_id: int):
    """Task that shows which worker is processing it."""
    worker_name = f"Worker-{worker_id}"
    await asyncio.sleep(0.2)
    print(f"Task {task_id} processed by {worker_name}")
    return f"Task {task_id} by {worker_name}"

async def main():
    # Step 2: Set up the queue
    backend = SQLiteBackend("multi_worker_queue.db")
    serializer = CloudpickleSerializer()
    queue = TaskQueue(backend, serializer)
    await queue.connect()

    print("=== Multiple Workers Example ===\n")

    # Step 3: Create multiple workers with different configurations
    workers = [
        Worker(backend, serializer, concurrency=1),  # Single-threaded worker
        Worker(backend, serializer, concurrency=2),  # Worker with concurrency 2
        Worker(backend, serializer, concurrency=1),  # Another single-threaded worker
    ]

    # Give each worker an ID for identification
    worker_ids = ["A", "B", "C"]
    for i, worker in enumerate(workers):
        worker.worker_id = worker_ids[i]

    # Step 4: Start all workers
    print("Starting all workers...")
    start_tasks = [worker.start() for worker in workers]
    await asyncio.gather(*start_tasks)

    # Step 5: Enqueue a mix of different tasks
    print("\nEnqueuing tasks...")
    task_ids = []

    # Queue some quick tasks
    for i in range(4):
        task_id = await queue.enqueue(quick_task, i)
        task_ids.append(task_id)

    # Queue some medium tasks
    for i in range(4, 8):
        task_id = await queue.enqueue(medium_task, i)
        task_ids.append(task_id)

    # Queue some slow tasks
    for i in range(8, 12):
        task_id = await queue.enqueue(slow_task, i)
        task_ids.append(task_id)

    print(f"Enqueued {len(task_ids)} tasks total")

    # Step 6: Demonstrate worker-specific tasks
    print("\nEnqueuing worker-specific tasks...")
    for i in range(12, 15):
        # Enqueue to specific worker using different approaches
        task_id = await queue.enqueue(worker_info, workers[0].worker_id, i)
        task_ids.append(task_id)

    # Step 7: Monitor progress and wait for completion
    print("\nProcessing tasks with multiple workers...")
    await asyncio.sleep(5)  # Give workers time to process

    # Step 8: Stop all workers
    print("\nStopping all workers...")
    stop_tasks = [worker.stop() for worker in workers]
    await asyncio.gather(*stop_tasks)

    # Step 9: Clean up
    await queue.close()
    print("=== Example completed ===")

async def demo_single_vs_multiple_workers():
    """Demonstrate the performance difference between single and multiple workers."""
    print("\n" + "="*50)
    print("PERFORMANCE COMPARISON: Single vs Multiple Workers")
    print("="*50)

    # Test with single worker
    print("\n1. Testing with single worker...")
    backend1 = SQLiteBackend("single_worker.db")
    serializer = CloudpickleSerializer()
    queue1 = TaskQueue(backend1, serializer)
    await queue1.connect()

    single_worker = Worker(backend1, serializer, concurrency=1)
    await single_worker.start()

    # Enqueue multiple tasks
    start_time = time.time()
    for i in range(6):
        await queue1.enqueue(slow_task, i)

    await asyncio.sleep(8)  # Wait for all tasks
    single_duration = time.time() - start_time

    await single_worker.stop()
    await queue1.close()

    # Test with multiple workers
    print("\n2. Testing with multiple workers...")
    backend2 = SQLiteBackend("multiple_workers.db")
    queue2 = TaskQueue(backend2, serializer)
    await queue2.connect()

    workers = [
        Worker(backend2, serializer, concurrency=1),
        Worker(backend2, serializer, concurrency=1),
        Worker(backend2, serializer, concurrency=1),
    ]

    await asyncio.gather(*[worker.start() for worker in workers])

    start_time = time.time()
    for i in range(6, 12):
        await queue2.enqueue(slow_task, i)

    await asyncio.sleep(8)  # Wait for all tasks
    multiple_duration = time.time() - start_time

    await asyncio.gather(*[worker.stop() for worker in workers])
    await queue2.close()

    # Results
    print(f"\nResults:")
    print(f"Single worker: {single_duration:.2f} seconds")
    print(f"Multiple workers: {multiple_duration:.2f} seconds")
    print(f"Speedup: {single_duration/multiple_duration:.2f}x")

if __name__ == "__main__":
    async def run_all():
        await main()
        await demo_single_vs_multiple_workers()

    asyncio.run(run_all())
```

## Key Concepts

### Worker Concurrency
Each worker has a `concurrency` setting that controls how many tasks it can process simultaneously:

- **concurrency=1**: Processes tasks one at a time
- **concurrency=N**: Can process up to N tasks concurrently
- Higher concurrency = better throughput but more resource usage

### Worker Coordination
Multiple workers automatically coordinate through the backend:

- **No Double Processing**: Tasks are atomically reserved by one worker
- **Load Balancing**: Work is distributed across available workers
- **Fault Tolerance**: If one worker fails, others continue processing

### Performance Considerations

**When to use multiple workers:**
- CPU-bound tasks (multiple workers can utilize multiple CPU cores)
- I/O-bound tasks (can overlap waiting times)
- High-throughput requirements

**When to avoid:**
- Tasks are very quick (overhead may exceed benefits)
- Limited system resources
- Tasks require shared state that isn't concurrency-safe

## Try It Yourself

1. **Experiment with different concurrency settings:**
   ```python
   # Test different concurrency levels
   for concurrency in [1, 2, 4, 8]:
       worker = Worker(backend, serializer, concurrency=concurrency)
       # Measure performance
   ```

2. **Test CPU-bound vs I/O-bound tasks:**
   - CPU-bound: Add numbers, sort lists, calculate fibonacci
   - I/O-bound: File operations, HTTP requests, database calls

3. **Monitor worker utilization:**
   - Add logging to see which workers process which tasks
   - Track processing times for different task types

## Next Steps

- Learn about [Task Results](./task-results.md) to retrieve outputs from multiple workers
- Explore [Batch Processing](./batch-processing.md) for efficient bulk operations
- See [Sync vs Async](./sync-async.md) for different programming models