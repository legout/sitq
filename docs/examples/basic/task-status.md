# Task Status

Learn how to monitor task progress, track queue statistics, and implement real-time status monitoring for your task queue.

## What You'll Learn

- How to check individual task status (pending, processing, completed)
- Monitoring queue statistics and performance metrics
- Real-time task progress tracking
- Building status dashboards and monitoring systems

## Prerequisites

- Complete [Task Results](./task-results.md) first
- Understanding of task lifecycle concepts

## Code Example

```python
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sitq import TaskQueue, Worker, Result
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer

# Step 1: Define tasks with different execution times
async def quick_processing_task(task_id: int):
    """A task that completes quickly."""
    await asyncio.sleep(0.5)
    print(f"✓ Quick task {task_id} completed")
    return f"Quick result {task_id}"

async def medium_processing_task(task_id: int):
    """A task that takes medium time."""
    await asyncio.sleep(2.0)
    print(f"✓ Medium task {task_id} completed")
    return f"Medium result {task_id}"

async def long_processing_task(task_id: int):
    """A task that takes a long time."""
    await asyncio.sleep(5.0)
    print(f"✓ Long task {task_id} completed")
    return f"Long result {task_id}"

# Step 2: Task Status Tracker
class TaskStatusTracker:
    """Track and monitor task status in real-time."""

    def __init__(self):
        self.task_info: Dict[str, dict] = {}
        self.status_history: Dict[str, List[tuple]] = {}

    def register_task(self, task_id: str, task_type: str, created_at: datetime = None):
        """Register a new task for tracking."""
        if created_at is None:
            created_at = datetime.now()

        self.task_info[task_id] = {
            "task_id": task_id,
            "task_type": task_type,
            "created_at": created_at,
            "status": "pending",
            "started_at": None,
            "finished_at": None,
            "result": None,
            "error": None
        }
        self.status_history[task_id] = [(created_at, "pending")]

    def update_status(self, task_id: str, status: str, timestamp: datetime = None, **kwargs):
        """Update task status and record history."""
        if timestamp is None:
            timestamp = datetime.now()

        if task_id in self.task_info:
            self.task_info[task_id]["status"] = status
            self.task_info[task_id].update(kwargs)
            self.status_history[task_id].append((timestamp, status))

    def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get current status of a specific task."""
        return self.task_info.get(task_id)

    def get_all_tasks(self) -> Dict[str, dict]:
        """Get status of all tracked tasks."""
        return self.task_info.copy()

    def get_queue_statistics(self) -> dict:
        """Calculate queue statistics."""
        total_tasks = len(self.task_info)
        if total_tasks == 0:
            return {"total": 0, "pending": 0, "processing": 0, "completed": 0, "failed": 0}

        status_counts = {"pending": 0, "processing": 0, "completed": 0, "failed": 0}

        for task_info in self.task_info.values():
            status = task_info["status"]
            if status in status_counts:
                status_counts[status] += 1

        return {
            "total": total_tasks,
            "pending": status_counts["pending"],
            "processing": status_counts["processing"],
            "completed": status_counts["completed"],
            "failed": status_counts["failed"]
        }

    def print_status_report(self):
        """Print a formatted status report."""
        stats = self.get_queue_statistics()
        print(f"\n=== Queue Statistics ===")
        print(f"Total Tasks: {stats['total']}")
        print(f"Pending: {stats['pending']}")
        print(f"Processing: {stats['processing']}")
        print(f"Completed: {stats['completed']}")
        print(f"Failed: {stats['failed']}")

        if stats['total'] > 0:
            print(f"\n=== Individual Task Status ===")
            for task_id, info in self.task_info.items():
                duration = ""
                if info["started_at"]:
                    end_time = info["finished_at"] or datetime.now()
                    duration = f" (Duration: {(end_time - info['started_at']).total_seconds():.1f}s)"

                print(f"Task {task_id[:8]}... - {info['status']} - {info['task_type']}{duration}")

# Step 3: Status Monitor
class StatusMonitor:
    """Real-time monitor for task status updates."""

    def __init__(self, queue: TaskQueue, tracker: TaskStatusTracker):
        self.queue = queue
        self.tracker = tracker
        self.monitoring = False

    async def start_monitoring(self, check_interval: float = 0.5):
        """Start monitoring task status updates."""
        self.monitoring = True
        print(f"🔍 Started monitoring tasks (checking every {check_interval}s)")

        while self.monitoring:
            await self.check_task_statuses()
            await asyncio.sleep(check_interval)

    def stop_monitoring(self):
        """Stop the monitoring process."""
        self.monitoring = False
        print("🛑 Stopped monitoring")

    async def check_task_statuses(self):
        """Check and update status of all tracked tasks."""
        for task_id in list(self.tracker.task_info.keys()):
            task_info = self.tracker.get_task_status(task_id)
            if not task_info:
                continue

            current_status = task_info["status"]

            # Check if task is completed
            if current_status in ["pending", "processing"]:
                result = await self.queue.get_result(task_id, timeout=0.1)

                if result:
                    if result.is_success():
                        self.tracker.update_status(
                            task_id, "completed",
                            finished_at=result.finished_at,
                            result=result.value
                        )
                    elif result.is_failed():
                        self.tracker.update_status(
                            task_id, "failed",
                            finished_at=result.finished_at,
                            error=result.error
                        )
                elif current_status == "pending":
                    # Check if task has started processing (advanced: would need backend access)
                    pass

# Step 4: Main demonstration
async def main():
    backend = SQLiteBackend("status_tracking_queue.db")
    serializer = CloudpickleSerializer()
    queue = TaskQueue(backend, serializer)
    await queue.connect()

    # Set up tracking and monitoring
    tracker = TaskStatusTracker()
    monitor = StatusMonitor(queue, tracker)

    # Create workers
    workers = [
        Worker(backend, serializer, concurrency=2),
        Worker(backend, serializer, concurrency=1),
    ]

    # Start workers
    await asyncio.gather(*[worker.start() for worker in workers])

    print("=== Task Status Monitoring Example ===\n")

    # Step 5: Enqueue tasks with tracking
    tasks_to_enqueue = [
        ("quick", quick_processing_task, [1, 2]),
        ("medium", medium_processing_task, [3, 4]),
        ("long", long_processing_task, [5]),
    ]

    print("📝 Enqueueing tasks...")
    for task_type, task_func, task_ids in tasks_to_enqueue:
        for task_id in task_ids:
            enqueued_task_id = await queue.enqueue(task_func, task_id)
            tracker.register_task(enqueued_task_id, task_type)
            print(f"  Enqueued {task_type} task {task_id}: {enqueued_task_id[:8]}...")

    # Start monitoring in background
    monitoring_task = asyncio.create_task(monitor.start_monitoring())

    print(f"\n🚀 Started {len(workers)} workers and monitoring")
    print("📊 Monitoring task progress...\n")

    # Step 6: Simulate real-time monitoring
    for i in range(15):  # Monitor for 15 iterations
        await asyncio.sleep(1.0)

        # Update some tasks to "processing" status (simplified simulation)
        for task_id, info in tracker.get_all_tasks().items():
            if info["status"] == "pending" and info["started_at"] is None:
                # Simulate task starting (in real implementation, you'd detect this from backend)
                if (datetime.now() - info["created_at"]).total_seconds() > 0.5:
                    tracker.update_status(task_id, "processing", started_at=datetime.now())

        # Print periodic status updates
        tracker.print_status_report()
        print()

    # Step 7: Final status check
    print("🔍 Performing final status check...")
    await asyncio.sleep(2.0)  # Allow time for final processing

    tracker.print_status_report()

    # Step 8: Performance analysis
    print("\n📈 Performance Analysis:")
    completed_tasks = [
        info for info in tracker.get_all_tasks().values()
        if info["status"] == "completed"
    ]

    if completed_tasks:
        durations = []
        for task in completed_tasks:
            if task["started_at"] and task["finished_at"]:
                duration = (task["finished_at"] - task["started_at"]).total_seconds()
                durations.append(duration)

        if durations:
            avg_duration = sum(durations) / len(durations)
            print(f"Average task duration: {avg_duration:.2f} seconds")
            print(f"Fastest task: {min(durations):.2f} seconds")
            print(f"Slowest task: {max(durations):.2f} seconds")

    # Step 9: Cleanup
    monitor.stop_monitoring()
    monitoring_task.cancel()

    await asyncio.gather(*[worker.stop() for worker in workers])
    await queue.close()

    print("\n✅ Status monitoring example completed!")

# Step 10: Batch Status Checker
async def check_multiple_task_status(task_ids: List[str], queue: TaskQueue):
    """Check status of multiple tasks efficiently."""
    results = {}

    # Use asyncio.gather for concurrent status checks
    async def check_single_task(task_id: str):
        result = await queue.get_result(task_id, timeout=0.1)
        return task_id, result

    # Check all tasks concurrently
    tasks = [check_single_task(task_id) for task_id in task_ids]
    completed_checks = await asyncio.gather(*tasks, return_exceptions=True)

    for task_id, result in completed_checks:
        if isinstance(result, Exception):
            results[task_id] = {"status": "error", "error": str(result)}
        elif result:
            if result.is_success():
                results[task_id] = {"status": "completed", "result": result.value}
            elif result.is_failed():
                results[task_id] = {"status": "failed", "error": result.error}
        else:
            results[task_id] = {"status": "pending"}

    return results

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Concepts

### Task Lifecycle States
- **Pending**: Task is enqueued and waiting for a worker
- **Processing**: Task is being executed by a worker
- **Completed**: Task finished successfully with a result
- **Failed**: Task encountered an error during execution

### Status Tracking Strategies
- **Polling**: Regularly check task status (used in this example)
- **Callbacks**: Use event-driven status updates (requires backend support)
- **Database Queries**: Direct database access for real-time status

### Queue Metrics
- **Throughput**: Tasks completed per time unit
- **Latency**: Time from enqueue to completion
- **Error Rate**: Percentage of failed tasks
- **Queue Depth**: Number of pending tasks

## Try It Yourself

1. **Create a real-time dashboard:**
   ```python
   import aiohttp
   from aiohttp import web

   async def status_api(request):
       stats = tracker.get_queue_statistics()
       return web.json_response(stats)
   ```

2. **Add performance alerts:**
   ```python
   if avg_duration > expected_duration:
       await send_alert(f"Task processing slower than expected: {avg_duration}s")
   ```

3. **Implement task prioritization:**
   - Track task priorities
   - Monitor high-priority task delays
   - Alert when critical tasks are stuck

## Best Practices

### Monitoring
- **Check Intervals**: Balance between real-time updates and system load
- **Batch Processing**: Check multiple tasks concurrently
- **Historical Data**: Track metrics over time for trend analysis

### Alerting
- **Thresholds**: Set realistic thresholds for alerts
- **Escalation**: Different alert levels for different severity
- **Recovery**: Clear alerts when issues are resolved

## Next Steps

- Learn about [Batch Processing](./batch-processing.md) for efficient bulk operations
- Explore [Sync vs Async](./sync-async.md) for different programming models
- See [Advanced Examples](../../advanced/) for production monitoring patterns