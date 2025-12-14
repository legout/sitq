# Batch Processing

Learn how to efficiently process large numbers of tasks using batch operations, bulk result collection, and optimized processing patterns.

## What You'll Learn

- Batch enqueueing multiple tasks efficiently
- Collecting results from many tasks simultaneously
- Processing data in chunks and batches
- Optimizing performance for bulk operations

## Prerequisites

- Complete [Task Arguments](./task-arguments.md) first
- Understanding of bulk data processing concepts

## Code Example

```python
import asyncio
import time
from typing import List, Dict, Any
from sitq import TaskQueue, Worker, Result
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer

# Step 1: Define tasks suitable for batch processing
async def process_item(item_id: int, data: Any):
    """Process a single item (simulates data transformation)."""
    await asyncio.sleep(0.1)  # Simulate processing time

    if isinstance(data, dict) and "value" in data:
        result = {
            "item_id": item_id,
            "original_value": data["value"],
            "processed_value": data["value"] * 2,
            "status": "processed",
            "timestamp": time.time()
        }
    else:
        result = {
            "item_id": item_id,
            "original_value": data,
            "processed_value": str(data).upper(),
            "status": "processed",
            "timestamp": time.time()
        }

    return result

async def validate_data(item_id: int, data: Dict[str, Any]):
    """Validate data and return validation results."""
    await asyncio.sleep(0.05)

    validation_result = {
        "item_id": item_id,
        "is_valid": True,
        "errors": [],
        "warnings": []
    }

    # Simple validation rules
    if "email" in data:
        email = data["email"]
        if "@" not in email:
            validation_result["errors"].append("Invalid email format")
            validation_result["is_valid"] = False

    if "age" in data:
        age = data["age"]
        if not isinstance(age, int) or age < 0 or age > 150:
            validation_result["errors"].append("Invalid age")
            validation_result["is_valid"] = False

    return validation_result

async def calculate_metrics(data: List[float]):
    """Calculate metrics for a batch of numbers."""
    await asyncio.sleep(0.2)

    if not data:
        return {"count": 0, "sum": 0, "average": 0}

    return {
        "count": len(data),
        "sum": sum(data),
        "average": sum(data) / len(data),
        "min": min(data),
        "max": max(data)
    }

# Step 2: Batch Processor Classes
class BatchProcessor:
    """Utility class for batch processing operations."""

    def __init__(self, queue: TaskQueue, worker: Worker):
        self.queue = queue
        self.worker = worker
        self.batch_size = 10

    async def enqueue_batch(
        self,
        task_func,
        batch_data: List[tuple],
        batch_size: int = None
    ) -> List[str]:
        """Enqueue a batch of tasks efficiently."""
        if batch_size is None:
            batch_size = self.batch_size

        task_ids = []

        # Process in chunks to avoid overwhelming the system
        for i in range(0, len(batch_data), batch_size):
            chunk = batch_data[i:i + batch_size]

            # Enqueue tasks in the current chunk concurrently
            chunk_tasks = []
            for args in chunk:
                if isinstance(args, tuple):
                    task_id = await self.queue.enqueue(task_func, *args)
                else:
                    task_id = await self.queue.enqueue(task_func, args)
                task_ids.append(task_id)
                chunk_tasks.append(task_id)

            # Small delay between chunks to prevent overwhelming
            if i + batch_size < len(batch_data):
                await asyncio.sleep(0.01)

        return task_ids

    async def collect_results(
        self,
        task_ids: List[str],
        timeout: float = 30.0,
        poll_interval: float = 0.5
    ) -> Dict[str, Result]:
        """Collect results from a batch of tasks."""
        results = {}
        remaining_ids = set(task_ids)

        start_time = time.time()

        while remaining_ids and (time.time() - start_time) < timeout:
            # Check all remaining tasks concurrently
            check_tasks = []
            for task_id in list(remaining_ids):
                check_tasks.append(self._safe_get_result(task_id))

            completed_checks = await asyncio.gather(*check_tasks, return_exceptions=True)

            # Process results
            for task_id, result in zip(remaining_ids, completed_checks):
                if isinstance(result, Exception):
                    # Task failed with exception
                    results[task_id] = result
                    remaining_ids.remove(task_id)
                elif result:
                    # Task completed (success or failure)
                    results[task_id] = result
                    remaining_ids.remove(task_id)

            # Wait before next polling round
            if remaining_ids:
                await asyncio.sleep(poll_interval)

        return results

    async def _safe_get_result(self, task_id: str):
        """Safely get result with timeout."""
        try:
            return await self.queue.get_result(task_id, timeout=1.0)
        except Exception as e:
            return e

# Step 3: Data Processing Pipeline
class DataProcessingPipeline:
    """Example data processing pipeline using batch operations."""

    def __init__(self, queue: TaskQueue, worker: Worker):
        self.queue = queue
        self.worker = worker
        self.batch_processor = BatchProcessor(queue, worker)

    async def process_user_data(self, users_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process user data in batches."""
        print(f"📊 Processing {len(users_data)} user records...")

        # Step 1: Validate all users
        validation_task_ids = await self.batch_processor.enqueue_batch(
            validate_data,
            [(i, user_data) for i, user_data in enumerate(users_data)]
        )

        print(f"✅ Enqueued {len(validation_task_ids)} validation tasks")

        # Wait for validations to complete
        validation_results = await self.batch_processor.collect_results(validation_task_ids)

        # Step 2: Filter valid users
        valid_users = []
        valid_indices = []

        for i, user_data in enumerate(users_data):
            task_id = validation_task_ids[i]
            result = validation_results.get(task_id)

            if result and hasattr(result, 'value') and result.value.get("is_valid", False):
                valid_users.append(user_data)
                valid_indices.append(i)

        print(f"✅ Validation complete: {len(valid_users)} valid users out of {len(users_data)}")

        # Step 3: Process valid users
        if valid_users:
            process_task_ids = await self.batch_processor.enqueue_batch(
                process_item,
                [(i, user_data) for i, user_data in enumerate(valid_users)]
            )

            print(f"⚙️  Enqueued {len(process_task_ids)} processing tasks")

            process_results = await self.batch_processor.collect_results(process_task_ids)

            # Step 4: Collect final results
            processed_users = []
            for i, task_id in enumerate(process_task_ids):
                result = process_results.get(task_id)
                if result and hasattr(result, 'value'):
                    processed_users.append(result.value)

            return {
                "total_users": len(users_data),
                "valid_users": len(valid_users),
                "processed_users": processed_users,
                "success_rate": len(valid_users) / len(users_data) if users_data else 0
            }

        return {"total_users": len(users_data), "valid_users": 0, "processed_users": [], "success_rate": 0}

    async def process_number_batches(self, number_batches: List[List[float]]) -> List[Dict[str, Any]]:
        """Process multiple batches of numbers."""
        print(f"🔢 Processing {len(number_batches)} number batches...")

        # Enqueue all batch processing tasks
        metrics_task_ids = await self.batch_processor.enqueue_batch(
            calculate_metrics,
            [(batch,) for batch in number_batches]
        )

        print(f"📈 Enqueued {len(metrics_task_ids)} metrics calculation tasks")

        # Collect all results
        metrics_results = await self.batch_processor.collect_results(metrics_task_ids)

        # Extract results
        batch_metrics = []
        for i, task_id in enumerate(metrics_task_ids):
            result = metrics_results.get(task_id)
            if result and hasattr(result, 'value'):
                batch_metrics.append({
                    "batch_id": i,
                    "metrics": result.value
                })

        return batch_metrics

# Step 4: Performance Monitor
class BatchPerformanceMonitor:
    """Monitor performance of batch operations."""

    def __init__(self):
        self.metrics = {
            "batches_processed": 0,
            "total_tasks": 0,
            "total_time": 0,
            "errors": 0
        }

    def record_batch(self, task_count: int, duration: float, error_count: int = 0):
        """Record metrics for a completed batch."""
        self.metrics["batches_processed"] += 1
        self.metrics["total_tasks"] += task_count
        self.metrics["total_time"] += duration
        self.metrics["errors"] += error_count

    def get_report(self) -> Dict[str, Any]:
        """Get performance report."""
        total_time = self.metrics["total_time"]
        total_tasks = self.metrics["total_tasks"]

        if total_time > 0 and total_tasks > 0:
            return {
                "batches_processed": self.metrics["batches_processed"],
                "total_tasks": total_tasks,
                "total_time_seconds": round(total_time, 2),
                "tasks_per_second": round(total_tasks / total_time, 2),
                "average_batch_time": round(total_time / self.metrics["batches_processed"], 2),
                "error_rate": round(self.metrics["errors"] / total_tasks * 100, 2) if total_tasks > 0 else 0
            }
        else:
            return self.metrics

# Step 5: Main demonstration
async def main():
    backend = SQLiteBackend("batch_processing_queue.db")
    serializer = CloudpickleSerializer()
    queue = TaskQueue(backend, serializer)
    await queue.connect()

    # Create multiple workers for better throughput
    workers = [
        Worker(backend, serializer, concurrency=3),
        Worker(backend, serializer, concurrency=2),
    ]

    await asyncio.gather(*[worker.start() for worker in workers])

    pipeline = DataProcessingPipeline(queue, workers[0])
    monitor = BatchPerformanceMonitor()

    print("=== Batch Processing Example ===\n")

    # Test 1: Process user data in batches
    print("1. User Data Processing:")

    # Create sample user data
    sample_users = [
        {"name": "Alice", "email": "alice@example.com", "age": 30},
        {"name": "Bob", "email": "bob@example.com", "age": 25},
        {"name": "Charlie", "email": "invalid-email", "age": 35},
        {"name": "Diana", "email": "diana@example.com", "age": -5},  # Invalid age
        {"name": "Eve", "email": "eve@example.com", "age": 28},
    ] * 4  # Create 20 users total

    start_time = time.time()
    user_results = await pipeline.process_user_data(sample_users)
    duration = time.time() - start_time

    monitor.record_batch(len(sample_users), duration)
    print(f"✅ User processing completed in {duration:.2f}s")
    print(f"   Results: {user_results}")

    # Test 2: Process number batches
    print("\n2. Number Batch Processing:")

    # Create sample number batches
    number_batches = [
        [1.1, 2.2, 3.3, 4.4, 5.5],
        [10, 20, 30, 40, 50],
        [0.1, 0.2, 0.3],
        [100, 200, 300, 400],
        [],  # Empty batch
    ] * 3  # Create 15 batches total

    start_time = time.time()
    batch_results = await pipeline.process_number_batches(number_batches)
    duration = time.time() - start_time

    monitor.record_batch(len(number_batches), duration)
    print(f"✅ Batch processing completed in {duration:.2f}s")
    print(f"   Processed {len(batch_results)} batches")

    # Test 3: Large batch processing
    print("\n3. Large Batch Processing:")

    # Create a large dataset
    large_dataset = [{"value": i, "category": f"item_{i % 10}"} for i in range(100)]

    start_time = time.time()
    large_task_ids = await pipeline.batch_processor.enqueue_batch(
        process_item,
        [(i, item) for i, item in enumerate(large_dataset)],
        batch_size=20
    )
    duration = time.time() - start_time

    print(f"📤 Enqueued {len(large_task_ids)} tasks in {duration:.2f}s")

    # Collect results
    start_time = time.time()
    large_results = await pipeline.batch_processor.collect_results(large_task_ids)
    duration = time.time() - start_time

    success_count = sum(1 for r in large_results.values() if hasattr(r, 'value'))
    monitor.record_batch(len(large_dataset), duration)

    print(f"📥 Collected {success_count} results in {duration:.2f}s")

    # Test 4: Performance report
    print("\n4. Performance Summary:")
    report = monitor.get_report()
    for key, value in report.items():
        print(f"   {key}: {value}")

    # Cleanup
    await asyncio.gather(*[worker.stop() for worker in workers])
    await queue.close()

    print("\n✅ Batch processing example completed!")

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Concepts

### Batch Processing Strategies
- **Chunking**: Process data in manageable chunks
- **Concurrency**: Execute multiple tasks simultaneously
- **Batching**: Group similar operations for efficiency
- **Streaming**: Process data as it arrives

### Performance Optimization
- **Batch Size**: Find optimal balance between memory usage and throughput
- **Concurrency Limits**: Prevent overwhelming system resources
- **Result Collection**: Use efficient polling and aggregation
- **Error Handling**: Handle partial failures gracefully

### Use Cases
- **Data Transformation**: Process large datasets
- **Validation**: Validate many records simultaneously
- **Report Generation**: Generate multiple reports in parallel
- **Image Processing**: Process images in batches

## Best Practices

### Batch Sizing
```python
# For CPU-bound tasks
small_batches = 5-10 items per batch

# For I/O-bound tasks
large_batches = 50-100 items per batch

# Adjust based on task complexity and system resources
```

### Error Handling
```python
try:
    results = await batch_processor.collect_results(task_ids)
    successful_results = [r for r in results.values() if hasattr(r, 'value')]
    failed_results = [r for r in results.values() if not hasattr(r, 'value')]
except Exception as e:
    # Handle batch-level errors
    logger.error(f"Batch processing failed: {e}")
```

## Try It Yourself

1. **Experiment with different batch sizes:**
   - Test performance with batch sizes of 1, 10, 50, 100
   - Find the optimal batch size for your use case

2. **Create a data pipeline:**
   - Read data from files or databases
   - Process in multiple stages with batch operations
   - Write results back to storage

3. **Add progress tracking:**
   - Track progress of large batches
   - Show real-time progress updates
   - Estimate completion time

## Next Steps

- Learn about [Sync vs Async](./sync-async.md) for different programming models
- Explore [Error Handling](./error-handling.md) for robust batch processing
- See [Advanced Examples](../../advanced/) for production batch patterns