# CPU-Bound Task Processing

This example demonstrates how to handle CPU-intensive tasks using the ProcessWorker for better performance.

## Code Example

**`cpu_task_example.py`**
```python
import asyncio
import time
from sitq import TaskQueue, Worker, Result
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer

# A CPU-bound function
def compute_fibonacci(n):
    """Calculate fibonacci number recursively (CPU-intensive)."""
    if n <= 1:
        return n
    else:
        return compute_fibonacci(n-1) + compute_fibonacci(n-2)

def sort_large_list(numbers):
    """Sort a large list of numbers (CPU-intensive)."""
    return sorted(numbers)

def matrix_multiplication(matrix_a, matrix_b):
    """Multiply two matrices (CPU-intensive)."""
    if not matrix_a or not matrix_b:
        return []

    rows_a, cols_a = len(matrix_a), len(matrix_a[0])
    rows_b, cols_b = len(matrix_b), len(matrix_b[0])

    if cols_a != rows_b:
        raise ValueError("Cannot multiply matrices")

    # Initialize result matrix
    result = [[0 for _ in range(cols_b)] for _ in range(rows_a)]

    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += matrix_a[i][k] * matrix_b[k][j]

    return result

async def main():
    backend = SQLiteBackend("cpu_tasks.db")
    serializer = CloudpickleSerializer()
    queue = TaskQueue(backend, serializer)

    # Use Worker with high concurrency for CPU-bound tasks
    worker = Worker(
        backend=backend,
        serializer=serializer,
        concurrency=2  # Run up to 2 CPU-bound tasks in parallel
    )

    await worker.start()

    print("=== CPU-Bound Task Processing Example ===\n")

    # Example 1: Fibonacci calculation
    print("1. Fibonacci Calculation:")
    print("Enqueuing CPU-intensive fibonacci tasks...")

    fib_tasks = []
    for n in [30, 32, 34, 35]:  # Smaller numbers for demo
        task_id = await queue.enqueue(compute_fibonacci, n)
        fib_tasks.append((task_id, n))

    # Wait and collect results
    await asyncio.sleep(10)  # Give time for CPU-intensive tasks

    for task_id, n in fib_tasks:
        result = await queue.get_result(task_id, timeout=20)
        if result and result.is_success():
            print(f"  Fibonacci({n}) = {result.value}")
        else:
            print(f"  Fibonacci({n}) failed or timed out")

    # Example 2: Large list sorting
    print("\n2. Large List Sorting:")
    large_list = list(range(10000, 0, -1))  # Reverse sorted list
    task_id = await queue.enqueue(sort_large_list, large_list)

    await asyncio.sleep(5)
    result = await queue.get_result(task_id, timeout=30)
    if result and result.is_success():
        sorted_list = result.value
        print(f"  Sorted {len(large_list)} numbers")
        print(f"  First 5: {sorted_list[:5]}")
        print(f"  Last 5: {sorted_list[-5:]}")
        print(f"  Is sorted: {sorted_list == sorted(sorted_list)}")
    else:
        print("  List sorting failed or timed out")

    # Example 3: Matrix multiplication
    print("\n3. Matrix Multiplication:")
    # Create small matrices for demo
    matrix_a = [[1, 2], [3, 4]]
    matrix_b = [[5, 6], [7, 8]]

    task_id = await queue.enqueue(matrix_multiplication, matrix_a, matrix_b)

    await asyncio.sleep(2)
    result = await queue.get_result(task_id, timeout=10)
    if result and result.is_success():
        result_matrix = result.value
        print(f"  Matrix A: {matrix_a}")
        print(f"  Matrix B: {matrix_b}")
        print(f"  Result: {result_matrix}")

        # Verify result
        expected = [[19, 22], [43, 50]]
        if result_matrix == expected:
            print("  ✓ Multiplication correct!")
        else:
            print("  ✗ Multiplication incorrect!")
    else:
        print("  Matrix multiplication failed")

    # Performance comparison
    print("\n4. Performance Analysis:")
    print("CPU-bound tasks benefit from:")
    print("  • Process isolation (no GIL limitations)")
    print("  • Multiple CPU cores utilization")
    print("  • Separate memory spaces")
    print("  • Better for truly parallel computations")

    await worker.stop()
    await queue.close()
    print("\n✅ CPU-bound processing example completed!")

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Concepts

### CPU-Bound vs I/O-Bound
- **CPU-Bound**: Tasks that spend time computing (fibonacci, sorting, math)
- **I/O-Bound**: Tasks that wait for external resources (database, network, file system)

### ProcessWorker vs ThreadWorker
- **ProcessWorker**: Best for CPU-bound tasks, uses separate processes
- **ThreadWorker**: Better for I/O-bound tasks, uses threads within same process

### Performance Tips
- Use multiple processes to utilize all CPU cores
- Limit concurrency to number of CPU cores for CPU-bound tasks
- Monitor memory usage with multiple processes
- Consider task granularity (don't make tasks too small)

## When to Use CPU-Bound Processing

✅ **Good for CPU-bound processing:**
- Mathematical calculations
- Data transformations
- Image/video processing
- Machine learning inference
- Cryptographic operations

❌ **Avoid for CPU-bound processing:**
- Simple I/O operations
- Network requests
- File system operations
- Database queries (unless computationally complex)