# CPU-bound Tasks

Learn how to efficiently handle CPU-intensive workloads with sitq using ProcessWorker, optimization techniques, and performance monitoring.

## What You'll Learn

- Understanding CPU-bound vs I/O-bound tasks
- Using ProcessWorker for true parallelism
- Optimizing CPU-intensive task processing
- Performance monitoring and tuning
- Memory management for intensive workloads

## Prerequisites

- Complete [Multiple Workers](../basic/multiple-workers.md) first
- Understanding of CPU vs I/O bound operations
- Basic knowledge of process vs thread execution

## Code Example

```python
import asyncio
import time
import multiprocessing
from typing import List, Dict, Any, Tuple
from concurrent.futures import ProcessPoolExecutor
from sitq import TaskQueue, Worker
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer

# Step 1: CPU-intensive task functions
def fibonacci_cpu(n: int) -> int:
    """CPU-intensive Fibonacci calculation."""
    if n <= 1:
        return n
    return fibonacci_cpu(n-1) + fibonacci_cpu(n-2)

def prime_factorization(n: int) -> List[int]:
    """CPU-intensive prime factorization."""
    if n < 2:
        return []
    
    factors = []
    divisor = 2
    
    while n > 1:
        while n % divisor == 0:
            factors.append(divisor)
            n //= divisor
        divisor += 1
    
    return factors

def matrix_multiply(size: int) -> Dict[str, Any]:
    """CPU-intensive matrix multiplication."""
    import random
    
    # Create random matrices
    matrix_a = [[random.random() for _ in range(size)] for _ in range(size)]
    matrix_b = [[random.random() for _ in range(size)] for _ in range(size)]
    
    # Multiply matrices
    result = [[0 for _ in range(size)] for _ in range(size)]
    
    for i in range(size):
        for j in range(size):
            for k in range(size):
                result[i][j] += matrix_a[i][k] * matrix_b[k][j]
    
    return {
        "size": size,
        "elements": size * size,
        "operations": size * size * size,
        "determinant": sum(sum(row) for row in result)  # Simplified
    }

def image_processing_simulation(image_data: List[List[int]], 
                          filter_size: int = 3) -> Dict[str, Any]:
    """Simulate CPU-intensive image processing."""
    height = len(image_data)
    width = len(image_data[0]) if height > 0 else 0
    
    # Apply convolution filter (simplified)
    filtered_image = []
    for i in range(height):
        row = []
        for j in range(width):
            # Simple blur filter
            pixel_sum = 0
            pixel_count = 0
            
            for di in range(-filter_size//2, filter_size//2 + 1):
                for dj in range(-filter_size//2, filter_size//2 + 1):
                    ni, nj = i + di, j + dj
                    if 0 <= ni < height and 0 <= nj < width:
                        pixel_sum += image_data[ni][nj]
                        pixel_count += 1
            
            row.append(pixel_sum // max(1, pixel_count))
        filtered_image.append(row)
    
    return {
        "original_size": f"{height}x{width}",
        "filter_size": filter_size,
        "pixels_processed": height * width,
        "processing_time_estimate": height * width * filter_size * filter_size
    }

def data_compression_simulation(data: List[int]) -> Dict[str, Any]:
    """Simulate CPU-intensive data compression."""
    if not data:
        return {"original_size": 0, "compressed_size": 0, "ratio": 0}
    
    # Simple run-length encoding simulation
    compressed = []
    current_value = data[0]
    count = 1
    
    for value in data[1:]:
        if value == current_value:
            count += 1
        else:
            compressed.append((current_value, count))
            current_value = value
            count = 1
    
    compressed.append((current_value, count))
    
    original_size = len(data)
    compressed_size = len(compressed) * 2  # Each pair is 2 values
    
    return {
        "original_size": original_size,
        "compressed_size": compressed_size,
        "compression_ratio": compressed_size / original_size,
        "unique_values": len(set(data))
    }

# Step 2: Performance monitoring
class CPUPerformanceMonitor:
    """Monitor CPU-intensive task performance."""
    
    def __init__(self):
        self.metrics = {
            "tasks_completed": 0,
            "total_cpu_time": 0,
            "total_wall_time": 0,
            "memory_usage": [],
            "task_types": {}
        }
    
    def start_task_timing(self, task_type: str):
        """Start timing a CPU task."""
        return {
            "task_type": task_type,
            "start_time": time.time(),
            "start_cpu": time.process_time()
        }
    
    def end_task_timing(self, timing_info: Dict[str, Any]) -> Dict[str, float]:
        """End timing and calculate metrics."""
        end_time = time.time()
        end_cpu = time.process_time()
        
        wall_time = end_time - timing_info["start_time"]
        cpu_time = end_cpu - timing_info["start_cpu"]
        
        # Update metrics
        self.metrics["tasks_completed"] += 1
        self.metrics["total_cpu_time"] += cpu_time
        self.metrics["total_wall_time"] += wall_time
        
        task_type = timing_info["task_type"]
        if task_type not in self.metrics["task_types"]:
            self.metrics["task_types"][task_type] = {
                "count": 0, "total_time": 0, "avg_time": 0
            }
        
        self.metrics["task_types"][task_type]["count"] += 1
        self.metrics["task_types"][task_type]["total_time"] += wall_time
        self.metrics["task_types"][task_type]["avg_time"] = (
            self.metrics["task_types"][task_type]["total_time"] / 
            self.metrics["task_types"][task_type]["count"]
        )
        
        return {
            "wall_time": wall_time,
            "cpu_time": cpu_time,
            "cpu_efficiency": cpu_time / wall_time if wall_time > 0 else 0
        }
    
    def get_report(self) -> Dict[str, Any]:
        """Get performance report."""
        total_tasks = self.metrics["tasks_completed"]
        if total_tasks == 0:
            return self.metrics
        
        return {
            **self.metrics,
            "avg_wall_time": self.metrics["total_wall_time"] / total_tasks,
            "avg_cpu_time": self.metrics["total_cpu_time"] / total_tasks,
            "overall_cpu_efficiency": (
                self.metrics["total_cpu_time"] / self.metrics["total_wall_time"]
                if self.metrics["total_wall_time"] > 0 else 0
            ),
            "throughput": total_tasks / max(1, self.metrics["total_wall_time"])
        }

# Step 3: Worker configuration optimization
class CPUWorkerOptimizer:
    """Optimize worker configuration for CPU tasks."""
    
    def __init__(self):
        self.cpu_count = multiprocessing.cpu_count()
        self.optimal_configs = {}
    
    def determine_optimal_config(self, task_complexity: str) -> Dict[str, int]:
        """Determine optimal worker configuration."""
        if task_complexity == "light":
            return {
                "worker_count": max(2, self.cpu_count // 2),
                "concurrency_per_worker": 2,
                "total_processes": self.cpu_count
            }
        elif task_complexity == "medium":
            return {
                "worker_count": self.cpu_count,
                "concurrency_per_worker": 1,
                "total_processes": self.cpu_count
            }
        elif task_complexity == "heavy":
            return {
                "worker_count": self.cpu_count,
                "concurrency_per_worker": 1,
                "total_processes": self.cpu_count
            }
        else:
            return {
                "worker_count": self.cpu_count,
                "concurrency_per_worker": 1,
                "total_processes": self.cpu_count
            }
    
    def create_optimized_workers(self, backend, serializer, config: Dict[str, int]):
        """Create optimized workers based on configuration."""
        workers = []
        
        for i in range(config["worker_count"]):
            worker = Worker(
                backend=backend,
                serializer=serializer,
                max_concurrency=config["concurrency_per_worker"]
            )
            workers.append(worker)
        
        return workers

# Step 4: CPU-bound task demonstrations
async def demo_fibonacci_tasks():
    """Demonstrate Fibonacci calculation tasks."""
    print("=" * 60)
    print("FIBONACCI CPU TASKS")
    print("=" * 60)
    
    backend = SQLiteBackend("fibonacci_queue.db")
    serializer = CloudpickleSerializer()
    queue = TaskQueue(backend, serializer)
    await queue.connect()
    
    # Optimize for CPU-bound tasks
    optimizer = CPUWorkerOptimizer()
    config = optimizer.determine_optimal_config("medium")
    workers = optimizer.create_optimized_workers(backend, serializer, config)
    
    # Start all workers
    await asyncio.gather(*[worker.start() for worker in workers])
    
    monitor = CPUPerformanceMonitor()
    
    # Enqueue Fibonacci tasks with different complexities
    fibonacci_tasks = [20, 25, 30, 35, 40]  # Increasing complexity
    
    print(f"🧮 Processing {len(fibonacci_tasks)} Fibonacci tasks...")
    print(f"   Using {len(workers)} workers with {config['concurrency_per_worker']} concurrency each")
    
    task_timings = []
    for n in fibonacci_tasks:
        timing = monitor.start_task_timing("fibonacci")
        task_id = await queue.enqueue(fibonacci_cpu, n)
        task_timings.append((task_id, timing))
        print(f"   Enqueued Fibonacci({n}): {task_id[:8]}...")
    
    # Wait for completion and collect results
    await asyncio.sleep(10)  # Allow time for processing
    
    results = []
    for task_id, timing in task_timings:
        result = await queue.get_result(task_id, timeout=5)
        if result and result.is_success():
            perf = monitor.end_task_timing(timing)
            results.append({
                "input": result.value,
                "performance": perf
            })
            print(f"   ✅ Fibonacci completed: {result.value} "
                  f"({perf['wall_time']:.3f}s)")
    
    # Performance summary
    report = monitor.get_report()
    print(f"\n📊 Fibonacci Performance:")
    print(f"   Tasks completed: {len(results)}")
    print(f"   Average time: {report['avg_wall_time']:.3f}s")
    print(f"   CPU efficiency: {report['overall_cpu_efficiency']:.2f}")
    
    await asyncio.gather(*[worker.stop() for worker in workers])
    await queue.close()
    
    return results

async def demo_matrix_operations():
    """Demonstrate matrix multiplication tasks."""
    print("\n" + "=" * 60)
    print("MATRIX MULTIPLICATION CPU TASKS")
    print("=" * 60)
    
    backend = SQLiteBackend("matrix_queue.db")
    serializer = CloudpickleSerializer()
    queue = TaskQueue(backend, serializer)
    await queue.connect()
    
    optimizer = CPUWorkerOptimizer()
    config = optimizer.determine_optimal_config("heavy")
    workers = optimizer.create_optimized_workers(backend, serializer, config)
    
    await asyncio.gather(*[worker.start() for worker in workers])
    
    monitor = CPUPerformanceMonitor()
    
    # Matrix sizes for testing
    matrix_sizes = [10, 25, 50, 75, 100]
    
    print(f"🔢 Processing {len(matrix_sizes)} matrix multiplication tasks...")
    
    task_timings = []
    for size in matrix_sizes:
        timing = monitor.start_task_timing("matrix_multiply")
        task_id = await queue.enqueue(matrix_multiply, size)
        task_timings.append((task_id, timing))
        print(f"   Enqueued {size}x{size} matrix: {task_id[:8]}...")
    
    # Wait for completion
    await asyncio.sleep(15)
    
    results = []
    for task_id, timing in task_timings:
        result = await queue.get_result(task_id, timeout=10)
        if result and result.is_success():
            perf = monitor.end_task_timing(timing)
            results.append({
                "size": result.value["size"],
                "operations": result.value["operations"],
                "performance": perf
            })
            print(f"   ✅ Matrix {result.value['size']}x{result.value['size']} completed "
                  f"({perf['wall_time']:.3f}s, {result.value['operations']} ops)")
    
    # Performance analysis
    report = monitor.get_report()
    print(f"\n📊 Matrix Performance:")
    print(f"   Total operations: {sum(r['operations'] for r in results)}")
    print(f"   Average time: {report['avg_wall_time']:.3f}s")
    print(f"   Throughput: {report['throughput']:.2f} tasks/s")
    
    await asyncio.gather(*[worker.stop() for worker in workers])
    await queue.close()
    
    return results

async def demo_image_processing():
    """Demonstrate image processing tasks."""
    print("\n" + "=" * 60)
    print("IMAGE PROCESSING CPU TASKS")
    print("=" * 60)
    
    backend = SQLiteBackend("image_queue.db")
    serializer = CloudpickleSerializer()
    queue = TaskQueue(backend, serializer)
    await queue.connect()
    
    optimizer = CPUWorkerOptimizer()
    config = optimizer.determine_optimal_config("medium")
    workers = optimizer.create_optimized_workers(backend, serializer, config)
    
    await asyncio.gather(*[worker.start() for worker in workers])
    
    monitor = CPUPerformanceMonitor()
    
    # Generate test images
    test_images = []
    for i, size in enumerate([50, 100, 150, 200]):
        # Create random image data
        import random
        image = [[random.randint(0, 255) for _ in range(size)] for _ in range(size)]
        test_images.append((f"image_{i}", image, 3))
    
    print(f"🖼️  Processing {len(test_images)} image processing tasks...")
    
    task_timings = []
    for name, image_data, filter_size in test_images:
        timing = monitor.start_task_timing("image_processing")
        task_id = await queue.enqueue(image_processing_simulation, image_data, filter_size)
        task_timings.append((task_id, timing))
        print(f"   Enqueued {name}: {task_id[:8]}...")
    
    # Wait for completion
    await asyncio.sleep(12)
    
    results = []
    for task_id, timing in task_timings:
        result = await queue.get_result(task_id, timeout=8)
        if result and result.is_success():
            perf = monitor.end_task_timing(timing)
            results.append({
                "image_info": result.value,
                "performance": perf
            })
            print(f"   ✅ Image {result.value['original_size']} completed "
                  f"({perf['wall_time']:.3f}s)")
    
    # Performance summary
    report = monitor.get_report()
    total_pixels = sum(r['image_info']['pixels_processed'] for r in results)
    print(f"\n📊 Image Processing Performance:")
    print(f"   Total pixels processed: {total_pixels:,}")
    print(f"   Average time: {report['avg_wall_time']:.3f}s")
    print(f"   Pixels per second: {total_pixels / report['total_wall_time']:,.0f}")
    
    await asyncio.gather(*[worker.stop() for worker in workers])
    await queue.close()
    
    return results

async def demo_performance_comparison():
    """Compare different worker configurations for CPU tasks."""
    print("\n" + "=" * 60)
    print("WORKER CONFIGURATION COMPARISON")
    print("=" * 60)
    
    # Test configurations
    configs = [
        ("Single Worker", 1, 1),
        ("Multiple Workers", multiprocessing.cpu_count(), 1),
        ("High Concurrency", 2, multiprocessing.cpu_count() // 2),
    ]
    
    test_task = lambda: fibonacci_cpu(30)  # Medium complexity task
    task_count = 8
    
    print(f"🧪 Testing {len(configs)} configurations with {task_count} tasks each...")
    
    for config_name, worker_count, concurrency in configs:
        print(f"\n📊 Testing {config_name}:")
        print(f"   Workers: {worker_count}, Concurrency: {concurrency}")
        
        backend = SQLiteBackend(f"perf_test_{config_name.lower().replace(' ', '_')}.db")
        serializer = CloudpickleSerializer()
        queue = TaskQueue(backend, serializer)
        await queue.connect()
        
        # Create workers
        workers = [
            Worker(backend, serializer, max_concurrency=concurrency)
            for _ in range(worker_count)
        ]
        
        await asyncio.gather(*[worker.start() for worker in workers])
        
        # Enqueue tasks
        start_time = time.time()
        task_ids = []
        
        for i in range(task_count):
            task_id = await queue.enqueue(test_task)
            task_ids.append(task_id)
        
        # Wait for completion
        completed_tasks = 0
        max_wait_time = 30
        wait_start = time.time()
        
        while completed_tasks < task_count and (time.time() - wait_start) < max_wait_time:
            for task_id in task_ids:
                result = await queue.get_result(task_id, timeout=1)
                if result and result.is_success():
                    completed_tasks += 1
                    task_ids.remove(task_id)
                    break
            
            if task_ids:  # Still tasks pending
                await asyncio.sleep(0.5)
        
        total_time = time.time() - start_time
        
        print(f"   ✅ Completed: {completed_tasks}/{task_count} tasks")
        print(f"   ⏱️  Total time: {total_time:.3f}s")
        print(f"   📈 Throughput: {completed_tasks / total_time:.2f} tasks/s")
        
        await asyncio.gather(*[worker.stop() for worker in workers])
        await queue.close()

async def demo_memory_management():
    """Demonstrate memory management for CPU tasks."""
    print("\n" + "=" * 60)
    print("MEMORY MANAGEMENT FOR CPU TASKS")
    print("=" * 60)
    
    backend = SQLiteBackend("memory_test.db")
    serializer = CloudpickleSerializer()
    queue = TaskQueue(backend, serializer)
    await queue.connect()
    
    # Use fewer workers to control memory usage
    worker_count = min(4, multiprocessing.cpu_count())
    workers = [
        Worker(backend, serializer, max_concurrency=1)
        for _ in range(worker_count)
    ]
    
    await asyncio.gather(*[worker.start() for worker in workers])
    
    monitor = CPUPerformanceMonitor()
    
    # Test with different data sizes
    data_sizes = [1000, 5000, 10000, 25000]
    
    print(f"💾 Testing memory management with different data sizes...")
    
    for size in data_sizes:
        print(f"\n📊 Testing with {size:,} data points:")
        
        # Create compression test data
        import random
        test_data = [random.randint(0, 100) for _ in range(size)]
        
        timing = monitor.start_task_timing("compression")
        task_id = await queue.enqueue(data_compression_simulation, test_data)
        
        # Wait for completion
        result = await queue.get_result(task_id, timeout=15)
        
        if result and result.is_success():
            perf = monitor.end_task_timing(timing)
            compression_info = result.value
            
            print(f"   ✅ Compression completed")
            print(f"      Original size: {compression_info['original_size']:,}")
            print(f"      Compressed size: {compression_info['compressed_size']:,}")
            print(f"      Compression ratio: {compression_info['compression_ratio']:.3f}")
            print(f"      Processing time: {perf['wall_time']:.3f}s")
        
        # Small delay between large tasks
        await asyncio.sleep(1)
    
    # Final memory report
    report = monitor.get_report()
    print(f"\n📊 Memory Management Summary:")
    print(f"   Tasks processed: {report['tasks_completed']}")
    print(f"   Average time: {report['avg_wall_time']:.3f}s")
    print(f"   CPU efficiency: {report['overall_cpu_efficiency']:.2f}")
    
    await asyncio.gather(*[worker.stop() for worker in workers])
    await queue.close()

async def main():
    """Run all CPU-bound task demonstrations."""
    print("🖥️  CPU-bound Tasks Examples for sitq")
    print("This demo shows how to efficiently handle CPU-intensive workloads.\n")
    
    await demo_fibonacci_tasks()
    await demo_matrix_operations()
    await demo_image_processing()
    await demo_performance_comparison()
    await demo_memory_management()
    
    print("\n✅ All CPU-bound task demos completed!")
    print("\n📚 Key Takeaways:")
    print("   • Use ProcessWorker for true CPU parallelism")
    print("   • Match worker count to CPU cores for CPU-bound tasks")
    print("   • Monitor CPU efficiency and memory usage")
    print("   • Optimize task granularity for best throughput")
    print("   • Consider batch processing for many small tasks")

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Concepts

### CPU-bound vs I/O-bound

**CPU-bound Tasks:**
- Limited by processor speed
- Benefit from true parallelism
- Examples: calculations, data processing, image processing
- Use ProcessWorker for best performance

**I/O-bound Tasks:**
- Limited by network/disk speed
- Benefit from concurrency
- Examples: API calls, database queries, file operations
- Use regular Worker with high concurrency

### ProcessWorker Advantages

- **True Parallelism**: Utilizes multiple CPU cores
- **Memory Isolation**: Each process has separate memory space
- **CPU Affinity**: Can bind processes to specific cores
- **Scalability**: Scales with number of CPU cores

### Performance Optimization

**Worker Configuration:**
```python
# For CPU-bound tasks
worker_count = multiprocessing.cpu_count()
concurrency_per_worker = 1  # One task per process

# For mixed workloads
worker_count = multiprocessing.cpu_count() // 2
concurrency_per_worker = 2  # Some concurrency per process
```

**Task Granularity:**
- **Fine-grained**: Many small tasks (better load balancing)
- **Coarse-grained**: Few large tasks (less overhead)
- **Optimal**: Balance based on your specific workload

## Best Practices

### Worker Configuration
```python
import multiprocessing

# Optimal for CPU-bound tasks
cpu_count = multiprocessing.cpu_count()
workers = [
    Worker(backend, serializer, max_concurrency=1)
    for _ in range(cpu_count)
]
```

### Memory Management
```python
# Process large datasets in chunks
def process_large_dataset(data, chunk_size=1000):
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        yield process_chunk(chunk)
```

### Performance Monitoring
```python
# Monitor CPU efficiency
cpu_time = time.process_time()
wall_time = time.time()

# ... do work ...

efficiency = (time.process_time() - cpu_time) / (time.time() - wall_time)
```

## Try It Yourself

1. **Test different worker configurations:**
   ```python
   # Compare single vs multiple processes
   configs = [
       (1, 4),    # 1 worker, 4 concurrency
       (4, 1),    # 4 workers, 1 concurrency each
       (2, 2)     # 2 workers, 2 concurrency each
   ]
   ```

2. **Optimize task granularity:**
   ```python
   # Test different batch sizes
   for batch_size in [10, 50, 100, 500]:
       await process_batch(data, batch_size)
   ```

3. **Monitor resource usage:**
   ```python
   import psutil
   
   def monitor_resources():
       print(f"CPU: {psutil.cpu_percent()}%")
       print(f"Memory: {psutil.virtual_memory().percent}%")
   ```

## Next Steps

- Explore [Backend Configuration](./backend-configuration.md) for optimization
- Learn about [Sync Wrapper](./sync-wrapper.md) for integration
- Review [Batch Processing](../basic/batch-processing.md) for efficiency patterns

## Related Advanced Examples

- [Backend Configuration](./backend-configuration.md) - Performance tuning
- [Sync Wrapper](./sync-wrapper.md) - Legacy integration