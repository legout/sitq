# Synchronous Wrapper

The synchronous wrapper provides a simplified interface for common use cases where you don't need the full complexity of asynchronous task processing.

## Basic Usage

### Simple Task Processing

```python
import asyncio
from sitq import SyncTaskQueue, SQLiteBackend

def process_data(data):
    """Process some data."""
    return f"Processed: {data}"

async def main():
    # Use the sync wrapper for simple cases
    with SyncTaskQueue(backend=SQLiteBackend("tasks.db")) as queue:
        # Enqueue a task (note: sync wrapper handles async internally)
        task_id = queue.enqueue(process_data, "test_data")
        print(f"Task enqueued: {task_id}")
        
        # Get result (blocks until completion)
        result = queue.get_result(task_id, timeout=5)
        if result and result.status == "success":
            value = queue.deserialize_result(result)
            print(f"Result: {value}")
        else:
            print(f"Task failed: {result.error if result else 'Unknown error'}")

if __name__ == "__main__":
    asyncio.run(main())
```

### One-shot Task Execution

```python
# Execute a single task and get result
def add_numbers(a, b):
    """Add two numbers."""
    return a + b

with sitq.SyncTaskQueue() as queue:
    result = queue.execute(add_numbers, 5, 3)  # Returns 8
    print(f"5 + 3 = {result}")
```

## Configuration Options

### Backend Configuration

```python
# Sync queue with custom backend
backend = SQLiteBackend("persistent.db")
with SyncTaskQueue(backend=backend) as queue:
    task_id = queue.enqueue(my_function, arg1, arg2)
    result = queue.get_result(task_id, timeout=5)
```

### Timeout Configuration

```python
# Set timeout for task execution
with sitq.SyncTaskQueue(timeout=30.0) as queue:
    try:
        result = queue.execute(long_running_task, data)
    except sitq.TaskTimeoutError:
        print("Task timed out")
```

## Advanced Patterns

### Batch Processing

```python
def process_batch(items):
    """Process a batch of items."""
    results = []
    
    with sitq.SyncTaskQueue() as queue:
        # Enqueue all tasks
        task_ids = []
        for item in items:
            task_id = queue.enqueue(sitq.Task(
                function=process_item,
                args=[item]
            ))
            task_ids.append(task_id)
        
        # Wait for all results
        for task_id in task_ids:
            result = queue.get_result(task_id)
            results.append(result.value)
    
    return results

# Process batch
items = ["item1", "item2", "item3"]
results = process_batch(items)
print(f"Processed {len(results)} items")
```

### Pipeline Processing

```python
def create_pipeline(stages):
    """Create a processing pipeline."""
    
    def pipeline_processor(data):
        """Process data through all stages."""
        current_data = data
        
        with sitq.SyncTaskQueue() as queue:
            for stage in stages:
                task_id = queue.enqueue(sitq.Task(
                    function=stage,
                    args=[current_data]
                ))
                result = queue.get_result(task_id)
                current_data = result.value
        
        return current_data
    
    return pipeline_processor

# Define pipeline stages
def stage1(data):
    """First processing stage."""
    return f"Stage1: {data}"

def stage2(data):
    """Second processing stage."""
    return f"Stage2: {data}"

def stage3(data):
    """Third processing stage."""
    return f"Stage3: {data}"

# Create and use pipeline
pipeline = create_pipeline([stage1, stage2, stage3])
result = pipeline("input data")
print(f"Pipeline result: {result}")
```

### Error Handling

```python
def safe_execute_with_retry(func, max_retries=3, retry_delay=1.0):
    """Execute function with retry logic."""
    
    for attempt in range(max_retries):
        try:
            with sitq.SyncTaskQueue() as queue:
                return queue.execute(func)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(retry_delay)

# Use with retry
result = safe_execute_with_retry(risky_function)
```

## Use Cases

### Data Processing Scripts

```python
def process_csv_file(input_path, output_path):
    """Process CSV file with sync wrapper."""
    import pandas as pd
    
    def load_data(path):
        """Load CSV data."""
        return pd.read_csv(path)
    
    def transform_data(df):
        """Transform data."""
        df['processed'] = df['value'] * 2
        return df
    
    def save_data(df, path):
        """Save processed data."""
        df.to_csv(path, index=False)
        return len(df)
    
    with sitq.SyncTaskQueue() as queue:
        # Load data
        load_task = queue.enqueue(sitq.Task(load_data, [input_path]))
        df = queue.get_result(load_task).value
        
        # Transform data
        transform_task = queue.enqueue(sitq.Task(transform_data, [df]))
        df = queue.get_result(transform_task).value
        
        # Save data
        save_task = queue.enqueue(sitq.Task(save_data, [df, output_path]))
        rows_saved = queue.get_result(save_task).value
    
    print(f"Processed and saved {rows_saved} rows")

# Use the function
process_csv_file("input.csv", "output.csv")
```

### Web Application Background Tasks

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_data():
    """Process data in background."""
    data = request.json
    
    def background_process(data):
        """Background processing function."""
        # Simulate processing
        time.sleep(5)
        return {"status": "completed", "result": data * 2}
    
    try:
        with sitq.SyncTaskQueue() as queue:
            result = queue.execute(background_process, data['value'])
            return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
```

### Scientific Computing

```python
def run_simulation(parameters):
    """Run scientific simulation."""
    import numpy as np
    
    def initialize_grid(size):
        """Initialize simulation grid."""
        return np.random.rand(size, size)
    
    def run_timestep(grid, dt):
        """Run single timestep."""
        return grid + dt * np.random.randn(*grid.shape)
    
    def analyze_results(grid):
        """Analyze simulation results."""
        return {
            "mean": float(np.mean(grid)),
            "std": float(np.std(grid)),
            "max": float(np.max(grid))
        }
    
    with sitq.SyncTaskQueue() as queue:
        # Initialize
        init_task = queue.enqueue(sitq.Task(initialize_grid, [parameters['size']]))
        grid = queue.get_result(init_task).value
        
        # Run simulation
        for step in range(parameters['steps']):
            timestep_task = queue.enqueue(sitq.Task(
                run_timestep, 
                [grid, parameters['dt']]
            ))
            grid = queue.get_result(timestep_task).value
        
        # Analyze results
        analysis_task = queue.enqueue(sitq.Task(analyze_results, [grid]))
        results = queue.get_result(analysis_task).value
    
    return results

# Run simulation
params = {"size": 100, "steps": 50, "dt": 0.01}
results = run_simulation(params)
print(f"Simulation results: {results}")
```

## Performance Considerations

### When to Use Sync Wrapper

**✅ Good for:**
- Simple scripts and utilities
- Data processing pipelines
- Prototyping and testing
- Sequential task dependencies
- Background tasks in web applications

**❌ Not ideal for:**
- High-concurrency scenarios
- Long-running background processes
- Complex task orchestration
- Real-time processing requirements

### Performance Optimization

```python
# Reuse queue for multiple tasks
class OptimizedProcessor:
    """Optimized processor that reuses queue."""
    
    def __init__(self, backend=None):
        self.backend = backend or sitq.SQLiteBackend(":memory:")
        self.queue = None
    
    def __enter__(self):
        self.queue = sitq.SyncTaskQueue(backend=self.backend)
        return self.queue.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.queue.__exit__(exc_type, exc_val, exc_tb)

# Use optimized processor
with OptimizedProcessor() as queue:
    for i in range(10):
        result = queue.execute(process_item, f"data_{i}")
        print(f"Processed {i}: {result}")
```

## Comparison with Async API

### Sync vs Async

```python
# Sync wrapper - simple and direct
with sitq.SyncTaskQueue() as queue:
    result = queue.execute(my_function, arg1, arg2)

# Async API - more control
queue = sitq.TaskQueue(backend=sitq.SQLiteBackend())
worker = sitq.Worker(queue)

task = sitq.Task(function=my_function, args=[arg1, arg2])
task_id = queue.enqueue(task)
result = worker.process_task(task_id)
```

### Migration Path

```python
# Start with sync wrapper
def simple_process(data):
    with sitq.SyncTaskQueue() as queue:
        return queue.execute(process_data, data)

# Migrate to async when needed
def advanced_process(data):
    queue = sitq.TaskQueue(backend=sitq.SQLiteBackend())
    worker = sitq.Worker(queue)
    
    # Can add more complex logic here
    task_id = queue.enqueue(sitq.Task(process_data, [data]))
    return worker.process_task(task_id).value
```

## Best Practices

1. **Use for simple cases** - Sync wrapper is perfect for straightforward task processing
2. **Keep tasks short** - Avoid long-running tasks that block the main thread
3. **Handle errors gracefully** - Always wrap in try-catch blocks
4. **Reuse queues** - For multiple tasks, consider reusing the same queue
5. **Monitor performance** - Check if sync wrapper meets your performance needs
6. **Migrate when needed** - Move to async API when you need more control

## Next Steps

- [Workers Guide](workers.md) - Explore worker configuration
- [API Reference](../reference/api/) - Detailed API documentation