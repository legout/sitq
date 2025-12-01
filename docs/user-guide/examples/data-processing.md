# Data Processing Pipeline

Learn how to build efficient data processing pipelines using sitq for handling large datasets and complex transformations.

## Overview

Data processing pipelines often involve:
- Reading data from various sources
- Transforming and cleaning data
- Processing data in parallel
- Aggregating results
- Writing processed data to destinations

sitq excels at orchestrating these workflows while providing reliability and scalability.

## Basic Data Processing Pipeline

### Simple ETL Pipeline

```python
import sitq
import pandas as pd
import time
from typing import List, Dict, Any

class DataPipeline:
    """Simple ETL pipeline using sitq."""
    
    def __init__(self, backend=None):
        self.backend = backend or sitq.SQLiteBackend("pipeline.db")
        self.queue = sitq.TaskQueue(backend=self.backend)
        self.worker = sitq.Worker(self.queue)
    
    def extract_data(self, source_path: str) -> List[Dict]:
        """Extract data from source."""
        print(f"Extracting data from {source_path}")
        
        # Simulate data extraction
        time.sleep(1)
        
        # In real scenario, this would read from database, API, file, etc.
        data = [
            {"id": i, "value": i * 2, "category": f"cat_{i % 3}"}
            for i in range(100)
        ]
        
        return data
    
    def transform_data(self, data: List[Dict]) -> List[Dict]:
        """Transform data."""
        print(f"Transforming {len(data)} records")
        
        # Simulate data transformation
        time.sleep(2)
        
        transformed = []
        for record in data:
            transformed_record = {
                "id": record["id"],
                "doubled_value": record["value"] * 2,
                "category_upper": record["category"].upper(),
                "processed_at": time.time()
            }
            transformed.append(transformed_record)
        
        return transformed
    
    def load_data(self, data: List[Dict], destination: str) -> int:
        """Load data to destination."""
        print(f"Loading {len(data)} records to {destination}")
        
        # Simulate data loading
        time.sleep(1)
        
        # In real scenario, this would write to database, file, API, etc.
        df = pd.DataFrame(data)
        df.to_csv(destination, index=False)
        
        return len(data)
    
    def run_pipeline(self, source_path: str, destination: str) -> Dict[str, Any]:
        """Run the complete pipeline."""
        print("Starting ETL pipeline...")
        
        # Extract
        extract_task = sitq.Task(
            function=self.extract_data,
            args=[source_path]
        )
        extract_id = self.queue.enqueue(extract_task)
        extract_result = self.worker.process_task(extract_id)
        data = extract_result.value
        
        # Transform
        transform_task = sitq.Task(
            function=self.transform_data,
            args=[data]
        )
        transform_id = self.queue.enqueue(transform_task)
        transform_result = self.worker.process_task(transform_id)
        transformed_data = transform_result.value
        
        # Load
        load_task = sitq.Task(
            function=self.load_data,
            args=[transformed_data, destination]
        )
        load_id = self.queue.enqueue(load_task)
        load_result = self.worker.process_task(load_id)
        
        return {
            "source_records": len(data),
            "transformed_records": len(transformed_data),
            "loaded_records": load_result.value,
            "destination": destination
        }

# Use the pipeline
pipeline = DataPipeline()
result = pipeline.run_pipeline("source.csv", "output.csv")
print(f"Pipeline completed: {result}")
```

## Parallel Data Processing

### Batch Processing with Multiple Workers

```python
import sitq
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import time

class ParallelDataProcessor:
    """Parallel data processor using sitq."""
    
    def __init__(self, num_workers=4):
        self.backend = sitq.SQLiteBackend("parallel_processing.db")
        self.queue = sitq.TaskQueue(backend=self.backend)
        self.workers = [
            sitq.Worker(self.queue, worker_id=f"worker_{i}")
            for i in range(num_workers)
        ]
    
    def process_chunk(self, chunk_data: List[Dict], chunk_id: int) -> Dict:
        """Process a chunk of data."""
        print(f"Processing chunk {chunk_id} with {len(chunk_data)} records")
        
        # Simulate processing time
        time.sleep(1)
        
        # Process each record
        processed = []
        for record in chunk_data:
            processed_record = {
                **record,
                "processed_value": record["value"] * np.random.rand(),
                "chunk_id": chunk_id,
                "processed_at": time.time()
            }
            processed.append(processed_record)
        
        return {
            "chunk_id": chunk_id,
            "processed_count": len(processed),
            "data": processed
        }
    
    def split_data(self, data: List[Dict], chunk_size: int) -> List[List[Dict]]:
        """Split data into chunks."""
        chunks = []
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            chunks.append(chunk)
        return chunks
    
    def process_data_parallel(self, data: List[Dict], chunk_size: int = 25) -> List[Dict]:
        """Process data in parallel chunks."""
        print(f"Processing {len(data)} records in parallel...")
        
        # Split data into chunks
        chunks = self.split_data(data, chunk_size)
        print(f"Split into {len(chunks)} chunks")
        
        # Start workers
        for worker in self.workers:
            worker.start()
        
        try:
            # Enqueue all chunks
            task_ids = []
            for i, chunk in enumerate(chunks):
                task = sitq.Task(
                    function=self.process_chunk,
                    args=[chunk, i]
                )
                task_id = self.queue.enqueue(task)
                task_ids.append(task_id)
            
            # Wait for all tasks to complete
            results = []
            for task_id in task_ids:
                result = self.queue.get_result(task_id, timeout=60)
                if result.is_error:
                    print(f"Task {task_id} failed: {result.error}")
                else:
                    results.append(result.value)
            
            # Combine results
            all_processed_data = []
            for result in results:
                all_processed_data.extend(result["data"])
            
            return all_processed_data
        
        finally:
            # Stop workers
            for worker in self.workers:
                worker.stop()
    
    def generate_sample_data(self, num_records: int = 1000) -> List[Dict]:
        """Generate sample data for processing."""
        return [
            {
                "id": i,
                "value": np.random.randn(),
                "category": np.random.choice(["A", "B", "C"]),
                "timestamp": time.time() - np.random.randint(0, 86400)
            }
            for i in range(num_records)
        ]

# Use parallel processor
processor = ParallelDataProcessor(num_workers=4)
sample_data = processor.generate_sample_data(1000)

start_time = time.time()
processed_data = processor.process_data_parallel(sample_data, chunk_size=50)
end_time = time.time()

print(f"Processed {len(processed_data)} records in {end_time - start_time:.2f} seconds")
```

## Advanced Pipeline Features

### Pipeline with Dependencies

```python
import sitq
from typing import List, Dict, Any
import time

class AdvancedPipeline:
    """Advanced pipeline with task dependencies."""
    
    def __init__(self):
        self.backend = sitq.SQLiteBackend("advanced_pipeline.db")
        self.queue = sitq.TaskQueue(backend=self.backend)
        self.worker = sitq.Worker(self.queue)
    
    def validate_data(self, data: List[Dict]) -> Dict[str, Any]:
        """Validate input data."""
        print("Validating data...")
        time.sleep(0.5)
        
        # Basic validation
        valid_records = []
        invalid_records = []
        
        for record in data:
            if "id" in record and "value" in record:
                valid_records.append(record)
            else:
                invalid_records.append(record)
        
        return {
            "valid_count": len(valid_records),
            "invalid_count": len(invalid_records),
            "valid_data": valid_records,
            "invalid_data": invalid_records
        }
    
    def clean_data(self, data: List[Dict]) -> List[Dict]:
        """Clean and normalize data."""
        print("Cleaning data...")
        time.sleep(1)
        
        cleaned = []
        for record in data:
            cleaned_record = {
                "id": int(record["id"]),
                "value": float(record["value"]),
                "category": str(record.get("category", "unknown")).strip().lower(),
                "cleaned_at": time.time()
            }
            cleaned.append(cleaned_record)
        
        return cleaned
    
    def enrich_data(self, data: List[Dict]) -> List[Dict]:
        """Enrich data with additional information."""
        print("Enriching data...")
        time.sleep(1.5)
        
        enriched = []
        for record in data:
            enriched_record = {
                **record,
                "value_category": "high" if record["value"] > 0 else "low",
                "id_length": len(str(record["id"])),
                "enriched_at": time.time()
            }
            enriched.append(enriched_record)
        
        return enriched
    
    def aggregate_data(self, data: List[Dict]) -> Dict[str, Any]:
        """Aggregate processed data."""
        print("Aggregating data...")
        time.sleep(0.5)
        
        # Calculate aggregations
        values = [record["value"] for record in data]
        categories = [record["category"] for record in data]
        
        category_counts = {}
        for category in categories:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "total_records": len(data),
            "value_stats": {
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "sum": sum(values)
            },
            "category_distribution": category_counts,
            "aggregated_at": time.time()
        }
    
    def run_advanced_pipeline(self, raw_data: List[Dict]) -> Dict[str, Any]:
        """Run advanced pipeline with dependencies."""
        print("Starting advanced pipeline...")
        
        # Step 1: Validate data
        validate_task = sitq.Task(function=self.validate_data, args=[raw_data])
        validate_id = self.queue.enqueue(validate_task)
        validate_result = self.worker.process_task(validate_id)
        validation_output = validate_result.value
        
        # Step 2: Clean valid data (depends on validation)
        clean_task = sitq.Task(
            function=self.clean_data,
            args=[validation_output["valid_data"]]
        )
        clean_id = self.queue.enqueue(clean_task, depends_on=[validate_id])
        clean_result = self.worker.process_task(clean_id)
        cleaned_data = clean_result.value
        
        # Step 3: Enrich data (depends on cleaning)
        enrich_task = sitq.Task(
            function=self.enrich_data,
            args=[cleaned_data]
        )
        enrich_id = self.queue.enqueue(enrich_task, depends_on=[clean_id])
        enrich_result = self.worker.process_task(enrich_id)
        enriched_data = enrich_result.value
        
        # Step 4: Aggregate data (depends on enrichment)
        aggregate_task = sitq.Task(
            function=self.aggregate_data,
            args=[enriched_data]
        )
        aggregate_id = self.queue.enqueue(aggregate_task, depends_on=[enrich_id])
        aggregate_result = self.worker.process_task(aggregate_id)
        aggregation_output = aggregate_result.value
        
        return {
            "validation": validation_output,
            "cleaning": {
                "records_processed": len(cleaned_data)
            },
            "enrichment": {
                "records_processed": len(enriched_data)
            },
            "aggregation": aggregation_output
        }

# Use advanced pipeline
pipeline = AdvancedPipeline()

# Generate sample data with some invalid records
sample_data = [
    {"id": i, "value": i * 0.1, "category": f"cat_{i % 3}"}
    for i in range(100)
] + [
    {"id": i, "value": i * 0.1}  # Missing category
    for i in range(100, 110)
] + [
    {"value": i * 0.1, "category": f"cat_{i % 3}"}  # Missing id
    for i in range(110, 115)
]

result = pipeline.run_advanced_pipeline(sample_data)
print(f"Pipeline completed: {result}")
```

## Real-time Data Processing

### Stream Processing with sitq

```python
import sitq
import time
import random
from typing import Iterator, Dict, Any
from collections import deque

class StreamProcessor:
    """Real-time stream processor using sitq."""
    
    def __init__(self, window_size=60):
        self.backend = sitq.SQLiteBackend("stream_processing.db")
        self.queue = sitq.TaskQueue(backend=self.backend)
        self.worker = sitq.Worker(self.queue)
        self.window_size = window_size  # Window size in seconds
        self.data_buffer = deque()
    
    def generate_stream_data(self) -> Iterator[Dict]:
        """Generate simulated stream data."""
        while True:
            data_point = {
                "timestamp": time.time(),
                "value": random.gauss(50, 10),
                "source": random.choice(["sensor_A", "sensor_B", "sensor_C"]),
                "event_type": random.choice(["measurement", "alert", "status"])
            }
            yield data_point
            time.sleep(0.1)  # 10 Hz data rate
    
    def process_window(self, window_data: List[Dict]) -> Dict[str, Any]:
        """Process a window of stream data."""
        print(f"Processing window with {len(window_data)} data points")
        
        # Calculate window statistics
        values = [point["value"] for point in window_data]
        sources = [point["source"] for point in window_data]
        
        source_counts = {}
        for source in sources:
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Detect anomalies (values > 3 std from mean)
        mean_val = sum(values) / len(values)
        std_val = (sum((x - mean_val) ** 2 for x in values) / len(values)) ** 0.5
        anomalies = [point for point in window_data 
                    if abs(point["value"] - mean_val) > 3 * std_val]
        
        return {
            "window_start": min(point["timestamp"] for point in window_data),
            "window_end": max(point["timestamp"] for point in window_data),
            "data_points": len(window_data),
            "statistics": {
                "mean": mean_val,
                "std": std_val,
                "min": min(values),
                "max": max(values)
            },
            "source_distribution": source_counts,
            "anomalies": {
                "count": len(anomalies),
                "data": anomalies
            },
            "processed_at": time.time()
        }
    
    def process_stream(self, duration: int = 300) -> None:
        """Process stream for specified duration."""
        print(f"Starting stream processing for {duration} seconds...")
        
        stream = self.generate_stream_data()
        start_time = time.time()
        window_start_time = start_time
        
        while time.time() - start_time < duration:
            # Collect data for current window
            current_window = []
            window_start_time = time.time()
            
            while time.time() - window_start_time < self.window_size:
                try:
                    data_point = next(stream)
                    current_window.append(data_point)
                except StopIteration:
                    break
            
            if current_window:
                # Process window asynchronously
                task = sitq.Task(
                    function=self.process_window,
                    args=[current_window]
                )
                task_id = self.queue.enqueue(task)
                
                # Get result (in real scenario, you might not wait)
                result = self.worker.process_task(task_id)
                window_result = result.value
                
                print(f"Window processed: {window_result['data_points']} points, "
                      f"{window_result['anomalies']['count']} anomalies")
        
        print("Stream processing completed")

# Use stream processor
processor = StreamProcessor(window_size=30)
processor.process_stream(duration=120)  # Process for 2 minutes
```

## Data Quality and Monitoring

### Quality Checks and Monitoring

```python
import sitq
import pandas as pd
from typing import List, Dict, Any, Tuple
import time

class DataQualityMonitor:
    """Data quality monitoring with sitq."""
    
    def __init__(self):
        self.backend = sitq.SQLiteBackend("quality_monitoring.db")
        self.queue = sitq.TaskQueue(backend=self.backend)
        self.worker = sitq.Worker(self.queue)
        self.quality_metrics = []
    
    def check_completeness(self, data: List[Dict], required_fields: List[str]) -> Dict[str, Any]:
        """Check data completeness."""
        print("Checking data completeness...")
        
        total_records = len(data)
        field_completeness = {}
        
        for field in required_fields:
            complete_count = sum(1 for record in data if field in record and record[field] is not None)
            field_completeness[field] = {
                "complete_count": complete_count,
                "completeness_rate": complete_count / total_records if total_records > 0 else 0
            }
        
        overall_completeness = sum(info["completeness_rate"] for info in field_completeness.values()) / len(field_completeness)
        
        return {
            "total_records": total_records,
            "field_completeness": field_completeness,
            "overall_completeness": overall_completeness,
            "passed": overall_completeness >= 0.95
        }
    
    def check_accuracy(self, data: List[Dict]) -> Dict[str, Any]:
        """Check data accuracy."""
        print("Checking data accuracy...")
        
        accuracy_issues = []
        
        for i, record in enumerate(data):
            # Check for negative IDs
            if "id" in record and record["id"] < 0:
                accuracy_issues.append({
                    "record_index": i,
                    "issue": "Negative ID",
                    "value": record["id"]
                })
            
            # Check for invalid categories
            if "category" in record and record["category"] not in ["A", "B", "C"]:
                accuracy_issues.append({
                    "record_index": i,
                    "issue": "Invalid category",
                    "value": record["category"]
                })
        
        accuracy_rate = 1 - (len(accuracy_issues) / len(data)) if data else 1
        
        return {
            "total_records": len(data),
            "accuracy_issues": accuracy_issues,
            "accuracy_rate": accuracy_rate,
            "passed": accuracy_rate >= 0.98
        }
    
    def check_consistency(self, data: List[Dict]) -> Dict[str, Any]:
        """Check data consistency."""
        print("Checking data consistency...")
        
        consistency_issues = []
        
        # Check for duplicate IDs
        ids = [record.get("id") for record in data if "id" in record]
        duplicate_ids = [id for id in set(ids) if ids.count(id) > 1]
        
        for dup_id in duplicate_ids:
            consistency_issues.append({
                "issue": "Duplicate ID",
                "value": dup_id,
                "count": ids.count(dup_id)
            })
        
        # Check for inconsistent timestamps
        timestamps = [record.get("timestamp") for record in data if "timestamp" in record]
        if timestamps:
            if max(timestamps) < min(timestamps):
                consistency_issues.append({
                    "issue": "Inconsistent timestamps",
                    "description": "Max timestamp is before min timestamp"
                })
        
        consistency_rate = 1 - (len(consistency_issues) / len(data)) if data else 1
        
        return {
            "total_records": len(data),
            "consistency_issues": consistency_issues,
            "consistency_rate": consistency_rate,
            "passed": consistency_rate >= 0.99
        }
    
    def run_quality_checks(self, data: List[Dict]) -> Dict[str, Any]:
        """Run all quality checks."""
        print("Running data quality checks...")
        
        required_fields = ["id", "value", "category", "timestamp"]
        
        # Run all checks
        completeness_task = sitq.Task(
            function=self.check_completeness,
            args=[data, required_fields]
        )
        completeness_id = self.queue.enqueue(completeness_task)
        completeness_result = self.worker.process_task(completeness_id)
        
        accuracy_task = sitq.Task(
            function=self.check_accuracy,
            args=[data]
        )
        accuracy_id = self.queue.enqueue(accuracy_task)
        accuracy_result = self.worker.process_task(accuracy_id)
        
        consistency_task = sitq.Task(
            function=self.check_consistency,
            args=[data]
        )
        consistency_id = self.queue.enqueue(consistency_task)
        consistency_result = self.worker.process_task(consistency_id)
        
        # Combine results
        overall_quality = {
            "completeness": completeness_result.value,
            "accuracy": accuracy_result.value,
            "consistency": consistency_result.value,
            "overall_score": (
                completeness_result.value["overall_completeness"] * 0.4 +
                accuracy_result.value["accuracy_rate"] * 0.3 +
                consistency_result.value["consistency_rate"] * 0.3
            ),
            "passed_all": (
                completeness_result.value["passed"] and
                accuracy_result.value["passed"] and
                consistency_result.value["passed"]
            ),
            "checked_at": time.time()
        }
        
        # Store quality metrics
        self.quality_metrics.append(overall_quality)
        
        return overall_quality
    
    def generate_quality_report(self) -> Dict[str, Any]:
        """Generate quality monitoring report."""
        if not self.quality_metrics:
            return {"message": "No quality metrics available"}
        
        latest = self.quality_metrics[-1]
        
        # Calculate trends
        if len(self.quality_metrics) > 1:
            previous = self.quality_metrics[-2]
            trend = {
                "completeness_change": latest["completeness"]["overall_completeness"] - previous["completeness"]["overall_completeness"],
                "accuracy_change": latest["accuracy"]["accuracy_rate"] - previous["accuracy"]["accuracy_rate"],
                "consistency_change": latest["consistency"]["consistency_rate"] - previous["consistency"]["consistency_rate"],
                "overall_change": latest["overall_score"] - previous["overall_score"]
            }
        else:
            trend = {}
        
        return {
            "latest_check": latest,
            "trend": trend,
            "total_checks": len(self.quality_metrics),
            "average_quality": sum(m["overall_score"] for m in self.quality_metrics) / len(self.quality_metrics)
        }

# Use quality monitor
monitor = DataQualityMonitor()

# Generate test data with quality issues
test_data = [
    {"id": i, "value": i * 0.1, "category": "A", "timestamp": time.time() + i}
    for i in range(50)
] + [
    {"id": i, "value": i * 0.1}  # Missing category and timestamp
    for i in range(50, 70)
] + [
    {"id": 25, "value": -5, "category": "X", "timestamp": time.time()}  # Duplicate ID, invalid category
]

# Run quality checks
quality_result = monitor.run_quality_checks(test_data)
print(f"Quality check completed: {quality_result['passed_all']}")

# Generate report
report = monitor.generate_quality_report()
print(f"Quality report: Overall score = {report['latest_check']['overall_score']:.2f}")
```

## Best Practices

### Performance Optimization

```python
# Optimize for large datasets
class OptimizedProcessor:
    """Optimized data processor for large datasets."""
    
    def __init__(self):
        self.backend = sitq.SQLiteBackend(
            "optimized_processing.db",
            connection_pool_size=20,
            enable_wal=True
        )
        self.queue = sitq.TaskQueue(backend=self.backend)
        self.workers = [
            sitq.Worker(self.queue, worker_id=f"worker_{i}")
            for i in range(8)  # More workers for CPU-bound tasks
        ]
    
    def process_large_dataset(self, data: List[Dict], chunk_size: int = 1000):
        """Process large dataset efficiently."""
        # Use larger chunks for better throughput
        chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
        
        # Start all workers
        for worker in self.workers:
            worker.start()
        
        try:
            # Batch enqueue for better performance
            tasks = [
                sitq.Task(function=self.process_chunk, args=[chunk, i])
                for i, chunk in enumerate(chunks)
            ]
            task_ids = self.queue.enqueue_batch(tasks)
            
            # Collect results
            results = []
            for task_id in task_ids:
                result = self.queue.get_result(task_id, timeout=300)
                results.append(result.value)
            
            return results
        
        finally:
            for worker in self.workers:
                worker.stop()
```

## Next Steps

- [Web Application Example](web-app.md) - Learn about web app integration
- [Microservices Example](microservices.md) - Explore microservices patterns
- [Error Handling Guide](../error-handling.md) - Comprehensive error management
- [Performance Guide](../performance.md) - Optimization techniques