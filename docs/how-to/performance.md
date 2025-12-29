# Performance Guide

This guide covers performance optimization, benchmarking, and tuning strategies for sitq.

## Performance Overview

### Key Performance Metrics

1. **Throughput**: Tasks processed per second
2. **Latency**: Time from task enqueue to completion
3. **Resource Usage**: CPU, memory, and I/O consumption
4. **Scalability**: Performance under increasing load
5. **Reliability**: Error rates and recovery times

### Performance Targets

| Metric | Target | Measurement |
|---------|--------|--------------|
| Task Throughput | > 100 tasks/sec | Simple tasks, single worker |
| Task Latency | < 100ms | End-to-end processing |
| Memory Usage | < 100MB | 1000 queued tasks |
| CPU Usage | < 50% | Normal operation |
| Error Rate | < 0.1% | Production environment |

## Benchmarking

### Benchmark Framework

```python
# benchmarks/benchmark_framework.py
import time
import statistics
import psutil
import os
from typing import List, Dict, Any, Callable
from dataclasses import dataclass

import sitq


@dataclass
class BenchmarkResult:
    """Benchmark result data."""
    name: str
    throughput: float
    avg_latency: float
    p95_latency: float
    p99_latency: float
    memory_usage_mb: float
    cpu_usage_percent: float
    error_rate: float


class BenchmarkRunner:
    """Framework for running performance benchmarks."""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
    
    def run_benchmark(
        self,
        name: str,
        benchmark_func: Callable,
        duration: float = 10.0,
        warmup: float = 2.0
    ) -> BenchmarkResult:
        """Run a single benchmark."""
        print(f"Running benchmark: {name}")
        
        # Warmup
        print("  Warming up...")
        start_time = time.time()
        while time.time() - start_time < warmup:
            benchmark_func()
        
        # Collect metrics
        print("  Collecting metrics...")
        start_time = time.time()
        start_memory = self.process.memory_info().rss
        
        latencies = []
        errors = 0
        total_tasks = 0
        
        while time.time() - start_time < duration:
            task_start = time.time()
            try:
                result = benchmark_func()
                latency = time.time() - task_start
                latencies.append(latency)
                total_tasks += 1
            except Exception:
                errors += 1
        
        end_time = time.time()
        end_memory = self.process.memory_info().rss
        
        # Calculate metrics
        actual_duration = end_time - start_time
        throughput = total_tasks / actual_duration
        
        if latencies:
            avg_latency = statistics.mean(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
            p99_latency = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
        else:
            avg_latency = p95_latency = p99_latency = 0
        
        memory_usage_mb = (end_memory - start_memory) / 1024 / 1024
        cpu_usage_percent = self.process.cpu_percent()
        error_rate = errors / total_tasks if total_tasks > 0 else 0
        
        return BenchmarkResult(
            name=name,
            throughput=throughput,
            avg_latency=avg_latency,
            p95_latency=p95_latency,
            p99_latency=p99_latency,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
            error_rate=error_rate
        )
    
    def run_comparison(self, benchmarks: Dict[str, Callable]) -> List[BenchmarkResult]:
        """Run multiple benchmarks for comparison."""
        results = []
        
        for name, func in benchmarks.items():
            result = self.run_benchmark(name, func)
            results.append(result)
        
        return results
    
    def print_results(self, results: List[BenchmarkResult]):
        """Print benchmark results in a formatted table."""
        print("\n" + "="*80)
        print("BENCHMARK RESULTS")
        print("="*80)
        print(f"{'Name':<30} {'Throughput':<12} {'Avg Latency':<12} {'P95 Latency':<12} {'Memory (MB)':<12}")
        print("-"*80)
        
        for result in results:
            print(f"{result.name:<30} "
                  f"{result.throughput:<12.2f} "
                  f"{result.avg_latency*1000:<12.2f} "
                  f"{result.p95_latency*1000:<12.2f} "
                  f"{result.memory_usage_mb:<12.2f}")
        
        print("="*80)


# Benchmark scenarios
def benchmark_simple_tasks():
    """Benchmark simple task processing."""
    backend = sitq.SQLiteBackend(":memory:")
    queue = sitq.TaskQueue(backend=backend)
    worker = sitq.Worker(queue)
    
    def run_task():
        task = sitq.Task(function=lambda x: x * 2, args=[5])
        task_id = queue.enqueue(task)
        result = worker.process_task(task_id)
        return result.value
    
    return run_task


def benchmark_cpu_intensive_tasks():
    """Benchmark CPU-intensive tasks."""
    backend = sitq.SQLiteBackend(":memory:")
    queue = sitq.TaskQueue(backend=backend)
    worker = sitq.Worker(queue)
    
    def run_task():
        task = sitq.Task(function=lambda n=100000: sum(range(n)), args=[])
        task_id = queue.enqueue(task)
        result = worker.process_task(task_id)
        return result.value
    
    return run_task


def benchmark_io_intensive_tasks():
    """Benchmark I/O-intensive tasks."""
    backend = sitq.SQLiteBackend(":memory:")
    queue = sitq.TaskQueue(backend=backend)
    worker = sitq.Worker(queue)
    
    def run_task():
        task = sitq.Task(function=lambda: time.sleep(0.01) or "done", args=[])
        task_id = queue.enqueue(task)
        result = worker.process_task(task_id)
        return result.value
    
    return run_task


def benchmark_batch_operations():
    """Benchmark batch task operations."""
    backend = sitq.SQLiteBackend(":memory:")
    queue = sitq.TaskQueue(backend=backend)
    worker = sitq.Worker(queue)
    
    def run_batch():
        # Create batch of tasks
        tasks = [
            sitq.Task(function=lambda x, i=i: x + i, args=[100])
            for i in range(10)
        ]
        
        # Enqueue batch
        task_ids = queue.enqueue_batch(tasks)
        
        # Process batch
        results = []
        for task_id in task_ids:
            result = worker.process_task(task_id)
            results.append(result.value)
        
        return results
    
    return run_batch


if __name__ == "__main__":
    runner = BenchmarkRunner()
    
    benchmarks = {
        "Simple Tasks": benchmark_simple_tasks(),
        "CPU-Intensive Tasks": benchmark_cpu_intensive_tasks(),
        "I/O-Intensive Tasks": benchmark_io_intensive_tasks(),
        "Batch Operations": benchmark_batch_operations()
    }
    
    results = runner.run_comparison(benchmarks)
    runner.print_results(results)
```

### Performance Profiling

```python
# benchmarks/profiling.py
import cProfile
import pstats
import io
from typing import Callable, Any

import sitq


def profile_function(func: Callable, *args, **kwargs) -> Any:
    """Profile a function and return results."""
    # Create profiler
    profiler = cProfile.Profile()
    
    # Run function with profiling
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()
    
    # Create stats object
    stats_stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stats_stream)
    
    # Sort and print stats
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
    
    print("Profiling Results:")
    print(stats_stream.getvalue())
    
    return result


def profile_task_processing():
    """Profile task processing performance."""
    backend = sitq.SQLiteBackend(":memory:")
    queue = sitq.TaskQueue(backend=backend)
    worker = sitq.Worker(queue)
    
    def process_many_tasks():
        """Process many tasks for profiling."""
        for i in range(100):
            task = sitq.Task(
                function=lambda x, i=i: x * i,
                args=[10]
            )
            task_id = queue.enqueue(task)
            worker.process_task(task_id)
    
    return profile_function(process_many_tasks)


if __name__ == "__main__":
    profile_task_processing()
```

## Optimization Strategies

### 1. Backend Optimization

#### SQLite Configuration

```python
# optimized_sqlite_backend.py
import sitq


def create_optimized_backend(db_path: str = "optimized.db") -> sitq.SQLiteBackend:
    """Create an optimized SQLite backend."""
    return sitq.SQLiteBackend(
        database=db_path,
        # Connection pooling
        connection_pool_size=20,
        max_overflow=10,
        connection_timeout=30.0,
        
        # SQLite optimizations
        enable_wal=True,              # Enable Write-Ahead Logging
        synchronous="NORMAL",          # Balance safety and performance
        cache_size=10000,             # Larger cache
        temp_store="MEMORY",          # Store temp tables in memory
        journal_mode="WAL",           # WAL journal mode
        
        # Performance tuning
        page_size=4096,              # Page size optimization
        mmap_size=268435456,        # 256MB memory-mapped I/O
    )


# Performance comparison
def compare_backend_performance():
    """Compare optimized vs default backend performance."""
    import time
    
    # Default backend
    default_backend = sitq.SQLiteBackend(":memory:")
    default_queue = sitq.TaskQueue(backend=default_backend)
    default_worker = sitq.Worker(default_queue)
    
    # Optimized backend
    optimized_backend = create_optimized_backend(":memory:")
    optimized_queue = sitq.TaskQueue(backend=optimized_backend)
    optimized_worker = sitq.Worker(optimized_queue)
    
    def benchmark_worker(worker, queue, name):
        """Benchmark worker performance."""
        start_time = time.time()
        
        for i in range(1000):
            task = sitq.Task(function=lambda x, i=i: x + i, args=[100])
            task_id = queue.enqueue(task)
            worker.process_task(task_id)
        
        end_time = time.time()
        duration = end_time - start_time
        throughput = 1000 / duration
        
        print(f"{name}: {throughput:.2f} tasks/sec")
        return throughput
    
    print("Backend Performance Comparison:")
    default_throughput = benchmark_worker(default_worker, default_queue, "Default")
    optimized_throughput = benchmark_worker(optimized_worker, optimized_queue, "Optimized")
    
    improvement = (optimized_throughput - default_throughput) / default_throughput * 100
    print(f"Performance improvement: {improvement:.1f}%")


if __name__ == "__main__":
    compare_backend_performance()
```

#### Connection Pooling

```python
# connection_pooling.py
import sitq
import threading
import time
from concurrent.futures import ThreadPoolExecutor


class PooledBackendManager:
    """Manager for pooled backend connections."""
    
    def __init__(self, db_path: str, pool_size: int = 10):
        self.db_path = db_path
        self.pool_size = pool_size
        self.backends = []
        self.lock = threading.Lock()
        
        # Initialize connection pool
        for i in range(pool_size):
            backend = sitq.SQLiteBackend(db_path)
            self.backends.append(backend)
    
    def get_backend(self) -> sitq.SQLiteBackend:
        """Get a backend from the pool."""
        with self.lock:
            if self.backends:
                return self.backends.pop()
            else:
                # Pool exhausted, create new connection
                return sitq.SQLiteBackend(self.db_path)
    
    def return_backend(self, backend: sitq.SQLiteBackend):
        """Return a backend to the pool."""
        with self.lock:
            if len(self.backends) < self.pool_size:
                self.backends.append(backend)
            else:
                # Pool full, close connection
                backend.close()


def benchmark_connection_pooling():
    """Benchmark connection pooling performance."""
    # Without pooling
    def without_pooling():
        backend = sitq.SQLiteBackend("test_no_pool.db")
        queue = sitq.TaskQueue(backend=backend)
        worker = sitq.Worker(queue)
        
        for i in range(100):
            task = sitq.Task(function=lambda x: x * 2, args=[i])
            task_id = queue.enqueue(task)
            worker.process_task(task_id)
        
        backend.close()
    
    # With pooling
    def with_pooling():
        pool_manager = PooledBackendManager("test_pool.db", pool_size=5)
        
        def worker_task():
            backend = pool_manager.get_backend()
            try:
                queue = sitq.TaskQueue(backend=backend)
                worker = sitq.Worker(queue)
                
                for i in range(20):  # 100 tasks / 5 workers
                    task = sitq.Task(function=lambda x: x * 2, args=[i])
                    task_id = queue.enqueue(task)
                    worker.process_task(task_id)
            finally:
                pool_manager.return_backend(backend)
        
        # Run with multiple threads
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker_task) for _ in range(5)]
            for future in futures:
                future.result()
    
    # Benchmark both approaches
    print("Connection Pooling Benchmark:")
    
    start_time = time.time()
    without_pooling()
    no_pool_time = time.time() - start_time
    
    start_time = time.time()
    with_pooling()
    pool_time = time.time() - start_time
    
    print(f"Without pooling: {no_pool_time:.2f}s")
    print(f"With pooling: {pool_time:.2f}s")
    print(f"Improvement: {(no_pool_time - pool_time) / no_pool_time * 100:.1f}%")


if __name__ == "__main__":
    benchmark_connection_pooling()
```

### 2. Worker Optimization

#### Multi-Worker Configuration

```python
# worker_optimization.py
import sitq
import time
import threading
from concurrent.futures import ThreadPoolExecutor


def optimize_worker_configuration():
    """Find optimal worker configuration."""
    backend = sitq.SQLiteBackend(":memory:")
    queue = sitq.TaskQueue(backend=backend)
    
    def benchmark_workers(num_workers: int, duration: float = 10.0) -> float:
        """Benchmark with specified number of workers."""
        # Create workers
        workers = [
            sitq.Worker(queue, worker_id=f"worker_{i}")
            for i in range(num_workers)
        ]
        
        # Enqueue tasks
        task_count = 1000
        tasks = [
            sitq.Task(function=lambda x, i=i: x + i, args=[100])
            for i in range(task_count)
        ]
        task_ids = queue.enqueue_batch(tasks)
        
        # Start workers
        def run_worker(worker):
            worker.run(duration=duration)
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(run_worker, worker)
                for worker in workers
            ]
            
            # Wait for duration
            time.sleep(duration)
            
            # Stop workers
            for worker in workers:
                worker.stop()
            
            # Wait for threads to finish
            for future in futures:
                future.cancel()
        
        # Count completed tasks
        completed = 0
        for task_id in task_ids:
            try:
                result = queue.get_result(task_id)
                if result.is_success:
                    completed += 1
            except sitq.TaskNotFoundError:
                pass
        
        return completed / duration  # Throughput
    
    print("Worker Configuration Optimization:")
    print("Workers\tThroughput (tasks/sec)")
    print("-" * 40)
    
    best_throughput = 0
    best_workers = 1
    
    for num_workers in [1, 2, 4, 8, 16]:
        throughput = benchmark_workers(num_workers)
        print(f"{num_workers}\t{throughput:.2f}")
        
        if throughput > best_throughput:
            best_throughput = throughput
            best_workers = num_workers
    
    print(f"\nOptimal configuration: {best_workers} workers")
    print(f"Best throughput: {best_throughput:.2f} tasks/sec")


if __name__ == "__main__":
    optimize_worker_configuration()
```

#### Task Batching

```python
# task_batching.py
import sitq
import time


def benchmark_task_batching():
    """Benchmark task batching performance."""
    backend = sitq.SQLiteBackend(":memory:")
    queue = sitq.TaskQueue(backend=backend)
    worker = sitq.Worker(queue)
    
    # Individual task processing
    def individual_processing():
        start_time = time.time()
        
        for i in range(100):
            task = sitq.Task(function=lambda x, i=i: x + i, args=[100])
            task_id = queue.enqueue(task)
            worker.process_task(task_id)
        
        return time.time() - start_time
    
    # Batch task processing
    def batch_processing():
        start_time = time.time()
        
        # Create batch
        tasks = [
            sitq.Task(function=lambda x, i=i: x + i, args=[100])
            for i in range(100)
        ]
        
        # Enqueue batch
        task_ids = queue.enqueue_batch(tasks)
        
        # Process batch
        for task_id in task_ids:
            worker.process_task(task_id)
        
        return time.time() - start_time
    
    print("Task Batching Benchmark:")
    
    individual_time = individual_processing()
    batch_time = batch_processing()
    
    print(f"Individual processing: {individual_time:.3f}s")
    print(f"Batch processing: {batch_time:.3f}s")
    print(f"Improvement: {(individual_time - batch_time) / individual_time * 100:.1f}%")


if __name__ == "__main__":
    benchmark_task_batching()
```

### 3. Serialization Optimization

#### Custom Serialization

```python
# serialization_optimization.py
import sitq
import pickle
import json
import gzip
import time
from typing import Any


class CompressedSerializer:
    """Compressed serializer for large objects."""
    
    def __init__(self, base_serializer=pickle, compression_threshold=1024):
        self.base_serializer = base_serializer
        self.compression_threshold = compression_threshold
    
    def dumps(self, obj: Any) -> bytes:
        """Serialize object with optional compression."""
        data = self.base_serializer.dumps(obj)
        
        if len(data) > self.compression_threshold:
            compressed = gzip.compress(data)
            # Add header to indicate compression
            return b"COMPRESSED:" + compressed
        
        return data
    
    def loads(self, data: bytes) -> Any:
        """Deserialize object with optional decompression."""
        if data.startswith(b"COMPRESSED:"):
            compressed = data[11:]  # Remove header
            decompressed = gzip.decompress(compressed)
            return self.base_serializer.loads(decompressed)
        
        return self.base_serializer.loads(data)


class FastJSONSerializer:
    """Fast JSON serializer for simple objects."""
    
    def dumps(self, obj: Any) -> bytes:
        """Serialize to JSON bytes."""
        return json.dumps(obj).encode('utf-8')
    
    def loads(self, data: bytes) -> Any:
        """Deserialize from JSON bytes."""
        return json.loads(data.decode('utf-8'))


def benchmark_serialization():
    """Benchmark different serialization strategies."""
    # Test data
    simple_data = {"value": 42, "name": "test"}
    large_data = {"values": list(range(10000)), "metadata": {"key": "value" * 1000}}
    
    serializers = {
        "Pickle": pickle,
        "JSON": FastJSONSerializer(),
        "Compressed": CompressedSerializer(),
    }
    
    print("Serialization Benchmark:")
    print(f"{'Serializer':<15} {'Simple (μs)':<15} {'Large (μs)':<15} {'Size (bytes)':<15}")
    print("-" * 65)
    
    for name, serializer in serializers.items():
        # Benchmark simple data
        start_time = time.time()
        for _ in range(1000):
            serialized = serializer.dumps(simple_data)
            deserialized = serializer.loads(serialized)
        simple_time = (time.time() - start_time) / 1000 * 1000000  # microseconds
        
        # Benchmark large data
        start_time = time.time()
        for _ in range(100):
            serialized = serializer.dumps(large_data)
            deserialized = serializer.loads(serialized)
        large_time = (time.time() - start_time) / 100 * 1000000  # microseconds
        
        # Get serialized size
        serialized_size = len(serializer.dumps(large_data))
        
        print(f"{name:<15} {simple_time:<15.2f} {large_time:<15.2f} {serialized_size:<15}")
    
    # Test with sitq
    print("\nSitq Integration Test:")
    
    for name, serializer in serializers.items():
        backend = sitq.SQLiteBackend(":memory:")
        queue = sitq.TaskQueue(backend=backend, serializer=serializer)
        worker = sitq.Worker(queue)
        
        start_time = time.time()
        
        for i in range(100):
            task = sitq.Task(function=lambda x, i=i: x + i, args=[large_data])
            task_id = queue.enqueue(task)
            worker.process_task(task_id)
        
        total_time = time.time() - start_time
        throughput = 100 / total_time
        
        print(f"{name}: {throughput:.2f} tasks/sec")


if __name__ == "__main__":
    benchmark_serialization()
```

## Memory Optimization

### Memory Management

```python
# memory_optimization.py
import sitq
import gc
import psutil
import os
import time
from typing import List


class MemoryMonitor:
    """Monitor memory usage during operations."""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.baseline = self.process.memory_info().rss
    
    def current_usage(self) -> float:
        """Get current memory usage in MB."""
        return (self.process.memory_info().rss - self.baseline) / 1024 / 1024
    
    def peak_usage(self) -> float:
        """Get peak memory usage in MB."""
        return self.process.memory_info().peak_wss / 1024 / 1024


def optimize_memory_usage():
    """Demonstrate memory optimization techniques."""
    monitor = MemoryMonitor()
    
    print("Memory Optimization Demo:")
    print(f"Baseline memory: {monitor.current_usage():.2f} MB")
    
    # Technique 1: Use generators instead of lists
    print("\n1. Generators vs Lists:")
    
    def create_tasks_list(count: int) -> List[sitq.Task]:
        """Create tasks as list (high memory)."""
        return [
            sitq.Task(function=lambda x, i=i: x + i, args=[100])
            for i in range(count)
        ]
    
    def create_tasks_generator(count: int):
        """Create tasks as generator (low memory)."""
        for i in range(count):
            yield sitq.Task(function=lambda x, i=i: x + i, args=[100])
    
    # Test list approach
    gc.collect()  # Clean up before test
    list_memory_before = monitor.current_usage()
    tasks_list = create_tasks_list(10000)
    list_memory_after = monitor.current_usage()
    list_memory_usage = list_memory_after - list_memory_before
    
    print(f"  List approach: {list_memory_usage:.2f} MB")
    
    # Test generator approach
    del tasks_list  # Clean up
    gc.collect()
    
    generator_memory_before = monitor.current_usage()
    tasks_generator = list(create_tasks_generator(10000))  # Convert to list for comparison
    generator_memory_after = monitor.current_usage()
    generator_memory_usage = generator_memory_after - generator_memory_before
    
    print(f"  Generator approach: {generator_memory_usage:.2f} MB")
    print(f"  Memory savings: {(list_memory_usage - generator_memory_usage):.2f} MB")
    
    # Technique 2: Process in batches
    print("\n2. Batch Processing:")
    
    backend = sitq.SQLiteBackend(":memory:")
    queue = sitq.TaskQueue(backend=backend)
    worker = sitq.Worker(queue)
    
    def process_all_at_once(task_count: int):
        """Process all tasks at once (high memory)."""
        tasks = [
            sitq.Task(function=lambda x, i=i: x + i, args=[100])
            for i in range(task_count)
        ]
        
        task_ids = queue.enqueue_batch(tasks)
        
        for task_id in task_ids:
            worker.process_task(task_id)
    
    def process_in_batches(task_count: int, batch_size: int):
        """Process tasks in batches (low memory)."""
        for batch_start in range(0, task_count, batch_size):
            batch_end = min(batch_start + batch_size, task_count)
            
            tasks = [
                sitq.Task(function=lambda x, i=i: x + i, args=[100])
                for i in range(batch_start, batch_end)
            ]
            
            task_ids = queue.enqueue_batch(tasks)
            
            for task_id in task_ids:
                worker.process_task(task_id)
            
            # Clear batch from memory
            del tasks
    
    # Test batch processing
    task_count = 5000
    batch_size = 500
    
    gc.collect()
    batch_memory_before = monitor.current_usage()
    
    start_time = time.time()
    process_in_batches(task_count, batch_size)
    batch_time = time.time() - start_time
    
    batch_memory_after = monitor.current_usage()
    batch_memory_usage = batch_memory_after - batch_memory_before
    
    print(f"  Batch processing: {batch_time:.2f}s, {batch_memory_usage:.2f} MB")
    
    # Technique 3: Explicit garbage collection
    print("\n3. Garbage Collection:")
    
    def process_with_gc(task_count: int):
        """Process with explicit garbage collection."""
        for i in range(task_count):
            task = sitq.Task(function=lambda x, i=i: x + i, args=[100])
            task_id = queue.enqueue(task)
            worker.process_task(task_id)
            
            # Periodic garbage collection
            if i % 100 == 0:
                gc.collect()
    
    gc.collect()
    gc_memory_before = monitor.current_usage()
    
    start_time = time.time()
    process_with_gc(1000)
    gc_time = time.time() - start_time
    
    gc_memory_after = monitor.current_usage()
    gc_memory_usage = gc_memory_after - gc_memory_before
    
    print(f"  With GC: {gc_time:.2f}s, {gc_memory_usage:.2f} MB")
    print(f"  Peak memory: {monitor.peak_usage():.2f} MB")


if __name__ == "__main__":
    optimize_memory_usage()
```

## Production Tuning

### Production Configuration

```python
# production_tuning.py
import sitq
import logging
import time
from typing import Dict, Any


class ProductionConfig:
    """Production-optimized configuration."""
    
    @staticmethod
    def create_optimized_backend(
        db_path: str,
        read_only: bool = False
    ) -> sitq.SQLiteBackend:
        """Create production-optimized backend."""
        return sitq.SQLiteBackend(
            database=db_path,
            
            # Connection management
            connection_pool_size=50,
            max_overflow=20,
            connection_timeout=60.0,
            pool_recycle=3600.0,  # Recycle connections every hour
            
            # SQLite optimizations
            enable_wal=True,
            synchronous="NORMAL",  # Balance safety and performance
            cache_size=50000,      # Large cache for production
            temp_store="MEMORY",
            journal_mode="WAL",
            
            # Performance settings
            page_size=4096,
            mmap_size=1073741824,  # 1GB memory-mapped I/O
            busy_timeout=30000,      # 30 second timeout
            
            # Read-only optimization
            readonly=read_only
        )
    
    @staticmethod
    def create_optimized_worker(
        queue: sitq.TaskQueue,
        worker_id: str = None
    ) -> sitq.Worker:
        """Create production-optimized worker."""
        return sitq.Worker(
            queue=queue,
            worker_id=worker_id,
            
            # Performance settings
            poll_interval=0.1,      # Responsive polling
            timeout=300.0,            # 5 minute task timeout
            max_tasks=10000,          # Restart after many tasks
            
            # Resource limits
            max_memory_mb=2048,       # 2GB memory limit
            max_cpu_percent=80.0,     # 80% CPU limit
            
            # Reliability settings
            max_retries=5,            # Robust retry
            retry_delay=1.0,          # Start with 1 second delay
            backoff_factor=2.0,        # Exponential backoff
            
            # Monitoring
            log_level=logging.INFO,
            log_performance=True,
            log_errors=True
        )


def production_performance_test():
    """Test production configuration performance."""
    print("Production Configuration Performance Test")
    print("=" * 50)
    
    # Create production setup
    backend = ProductionConfig.create_optimized_backend("production_test.db")
    queue = sitq.TaskQueue(backend=backend)
    worker = ProductionConfig.create_optimized_worker(queue, "prod_worker")
    
    # Test different task types
    task_scenarios = {
        "Simple Tasks": lambda: sitq.Task(function=lambda x: x * 2, args=[42]),
        "CPU Tasks": lambda: sitq.Task(function=lambda n=100000: sum(range(n)), args=[]),
        "I/O Tasks": lambda: sitq.Task(function=lambda: time.sleep(0.01) or "done", args=[]),
        "Memory Tasks": lambda: sitq.Task(function=lambda: list(range(1000)), args=[]),
    }
    
    for scenario_name, task_factory in task_scenarios.items():
        print(f"\nTesting {scenario_name}:")
        
        # Warmup
        for _ in range(10):
            task = task_factory()
            task_id = queue.enqueue(task)
            worker.process_task(task_id)
        
        # Benchmark
        start_time = time.time()
        task_count = 1000
        
        for i in range(task_count):
            task = task_factory()
            task_id = queue.enqueue(task)
            worker.process_task(task_id)
        
        duration = time.time() - start_time
        throughput = task_count / duration
        
        print(f"  Throughput: {throughput:.2f} tasks/sec")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Avg per task: {duration/task_count*1000:.2f}ms")
    
    # Get worker statistics
    stats = worker.get_stats()
    print(f"\nWorker Statistics:")
    print(f"  Tasks processed: {stats.tasks_processed}")
    print(f"  Tasks failed: {stats.tasks_failed}")
    print(f"  Success rate: {stats.success_rate:.2%}")
    print(f"  Average task time: {stats.avg_task_duration:.3f}s")
    
    # Get backend statistics
    backend_stats = backend.get_stats()
    print(f"\nBackend Statistics:")
    print(f"  Total tasks: {backend_stats.total_tasks}")
    print(f"  Queue size: {backend_stats.queue_size}")
    print(f"  Database size: {backend_stats.database_size_mb:.2f} MB")


if __name__ == "__main__":
    production_performance_test()
```

## Monitoring and Alerting

### Performance Monitoring

```python
# performance_monitoring.py
import sitq
import time
import threading
import statistics
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """Performance metrics data."""
    timestamp: float
    throughput: float
    avg_latency: float
    p95_latency: float
    error_rate: float
    queue_depth: int
    memory_usage_mb: float
    cpu_usage_percent: float


class PerformanceMonitor:
    """Monitor sitq performance in real-time."""
    
    def __init__(self, queue: sitq.TaskQueue, worker: sitq.Worker):
        self.queue = queue
        self.worker = worker
        self.metrics_history: List[PerformanceMetrics] = []
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval: float = 5.0):
        """Start performance monitoring."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        print(f"Started performance monitoring (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("Stopped performance monitoring")
    
    def _monitor_loop(self, interval: float):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Print current metrics
                print(f"[{time.strftime('%H:%M:%S')}] "
                      f"Throughput: {metrics.throughput:.1f} tasks/sec, "
                      f"Latency: {metrics.avg_latency*1000:.1f}ms, "
                      f"Queue: {metrics.queue_depth}, "
                      f"Errors: {metrics.error_rate:.1%}")
                
                # Check for performance issues
                self._check_alerts(metrics)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
            
            time.sleep(interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        # Get queue statistics
        queue_stats = self.queue.get_stats()
        
        # Get worker statistics
        worker_stats = self.worker.get_stats()
        
        # Calculate throughput (tasks per second over last interval)
        if self.metrics_history:
            last_metrics = self.metrics_history[-1]
            time_diff = time.time() - last_metrics.timestamp
            task_diff = worker_stats.tasks_processed - getattr(last_metrics, 'tasks_processed', 0)
            throughput = task_diff / time_diff if time_diff > 0 else 0
        else:
            throughput = 0
        
        # Calculate error rate
        total_tasks = worker_stats.tasks_processed + worker_stats.tasks_failed
        error_rate = worker_stats.tasks_failed / total_tasks if total_tasks > 0 else 0
        
        # Get system metrics
        import psutil
        import os
        process = psutil.Process(os.getpid())
        
        return PerformanceMetrics(
            timestamp=time.time(),
            throughput=throughput,
            avg_latency=worker_stats.avg_task_duration,
            p95_latency=worker_stats.p95_task_duration,
            error_rate=error_rate,
            queue_depth=queue_stats.queued_tasks,
            memory_usage_mb=process.memory_info().rss / 1024 / 1024,
            cpu_usage_percent=process.cpu_percent(),
            tasks_processed=worker_stats.tasks_processed
        )
    
    def _check_alerts(self, metrics: PerformanceMetrics):
        """Check for performance alerts."""
        alerts = []
        
        # Throughput alert
        if metrics.throughput < 10:  # Less than 10 tasks/sec
            alerts.append(f"LOW_THROUGHPUT: {metrics.throughput:.1f} tasks/sec")
        
        # Latency alert
        if metrics.avg_latency > 1.0:  # Greater than 1 second
            alerts.append(f"HIGH_LATENCY: {metrics.avg_latency:.2f}s")
        
        # Error rate alert
        if metrics.error_rate > 0.05:  # Greater than 5%
            alerts.append(f"HIGH_ERROR_RATE: {metrics.error_rate:.1%}")
        
        # Queue depth alert
        if metrics.queue_depth > 1000:  # More than 1000 tasks queued
            alerts.append(f"HIGH_QUEUE_DEPTH: {metrics.queue_depth} tasks")
        
        # Memory alert
        if metrics.memory_usage_mb > 1024:  # More than 1GB
            alerts.append(f"HIGH_MEMORY: {metrics.memory_usage_mb:.1f} MB")
        
        # Print alerts
        for alert in alerts:
            print(f"🚨 ALERT: {alert}")
    
    def get_summary(self, duration_minutes: int = 5) -> Dict[str, Any]:
        """Get performance summary for specified duration."""
        cutoff_time = time.time() - (duration_minutes * 60)
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {"message": "No metrics available"}
        
        throughputs = [m.throughput for m in recent_metrics]
        latencies = [m.avg_latency for m in recent_metrics]
        error_rates = [m.error_rate for m in recent_metrics]
        
        return {
            "duration_minutes": duration_minutes,
            "metrics_count": len(recent_metrics),
            "throughput": {
                "avg": statistics.mean(throughputs),
                "min": min(throughputs),
                "max": max(throughputs)
            },
            "latency": {
                "avg": statistics.mean(latencies),
                "min": min(latencies),
                "max": max(latencies)
            },
            "error_rate": {
                "avg": statistics.mean(error_rates),
                "min": min(error_rates),
                "max": max(error_rates)
            }
        }


def demo_performance_monitoring():
    """Demonstrate performance monitoring."""
    # Create setup
    backend = sitq.SQLiteBackend(":memory:")
    queue = sitq.TaskQueue(backend=backend)
    worker = sitq.Worker(queue)
    
    # Start monitoring
    monitor = PerformanceMonitor(queue, worker)
    monitor.start_monitoring(interval=2.0)
    
    # Generate load
    def load_generator():
        """Generate variable load for testing."""
        for i in range(300):  # 5 minutes of load
            if i % 50 == 0:  # Every 100 seconds, change load
                print(f"\nChanging load pattern...")
            
            # Variable task complexity
            if i % 30 < 10:  # Light load
                task = sitq.Task(function=lambda x: x * 2, args=[i])
            elif i % 30 < 20:  # Medium load
                task = sitq.Task(function=lambda n=10000: sum(range(n)), args=[])
            else:  # Heavy load
                task = sitq.Task(function=lambda: time.sleep(0.1), args=[])
            
            task_id = queue.enqueue(task)
            worker.process_task(task_id)
            
            time.sleep(0.1)  # 10 tasks per second
    
    # Start load generation in background
    load_thread = threading.Thread(target=load_generator, daemon=True)
    load_thread.start()
    
    # Let it run for a while
    time.sleep(30)
    
    # Get summary
    summary = monitor.get_summary(duration_minutes=1)
    print(f"\nPerformance Summary (last 1 minute):")
    print(f"  Avg throughput: {summary['throughput']['avg']:.1f} tasks/sec")
    print(f"  Avg latency: {summary['latency']['avg']:.3f}s")
    print(f"  Avg error rate: {summary['error_rate']['avg']:.1%}")
    
    # Stop monitoring
    monitor.stop_monitoring()


if __name__ == "__main__":
    demo_performance_monitoring()
```

## Best Practices

### Performance Checklist

1. **Backend Optimization**
   - [ ] Use WAL mode for better concurrency
   - [ ] Configure appropriate connection pool size
   - [ ] Enable memory-mapped I/O for large databases
   - [ ] Tune cache size based on available memory

2. **Worker Optimization**
   - [ ] Use appropriate number of workers
   - [ ] Configure task timeouts
   - [ ] Implement retry logic with exponential backoff
   - [ ] Monitor resource usage

3. **Serialization Optimization**
   - [ ] Choose appropriate serializer for data types
   - [ ] Use compression for large objects
   - [ ] Consider custom serializers for specific use cases

4. **Memory Management**
   - [ ] Process tasks in batches
   - [ ] Use generators instead of lists
   - [ ] Implement periodic garbage collection
   - [ ] Monitor memory usage

5. **Monitoring**
   - [ ] Track key performance metrics
   - [ ] Set up alerts for performance issues
   - [ ] Monitor resource utilization
   - [ ] Log performance data

## Next Steps

- [Contributing Guide](contributing.md) - Learn how to contribute
- [Testing Guide](testing.md) - Understand testing strategy
- [API Reference](../reference/api/sitq.md) - Detailed API documentation