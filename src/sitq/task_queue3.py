import sqlite3
import json
import pickle
import time
import threading
from datetime import datetime
from typing import Any, Callable, Optional, Union
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SerializationMethod(Enum):
    JSON = "json"
    PICKLE = "pickle"


class TaskQueue:
    def __init__(self, db_path: str = "task_queue.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        self._create_tables()
        self._running = False
        self._worker_thread = None

    def _create_tables(self):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    func TEXT NOT NULL,
                    args BLOB,
                    kwargs BLOB,
                    serialization_method TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    result BLOB,
                    error TEXT,
                    scheduled_time REAL,
                    created_time REAL NOT NULL,
                    completed_time REAL
                )
            """)
            self.conn.commit()

    def add_task(self, func: Union[Callable, str], *args, **kwargs) -> int:
        """Add a task to the queue. Returns task ID."""
        if isinstance(func, Callable):
            func_name = func.__name__
        else:
            func_name = func

        # Determine serialization method based on args/kwargs
        serialization_method = SerializationMethod.PICKLE
        try:
            json.dumps(list(args))
            json.dumps(kwargs)
            serialization_method = SerializationMethod.JSON
        except (TypeError, ValueError):
            pass  # Use pickle if JSON serialization fails

        # Serialize arguments
        if serialization_method == SerializationMethod.JSON:
            serialized_args = json.dumps(list(args))
            serialized_kwargs = json.dumps(kwargs)
        else:
            serialized_args = pickle.dumps(args)
            serialized_kwargs = pickle.dumps(kwargs)

        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO tasks (name, func, args, kwargs, serialization_method, 
                                  scheduled_time, created_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    func_name,
                    func_name,
                    serialized_args,
                    serialized_kwargs,
                    serialization_method.value,
                    kwargs.pop("_scheduled_time", None),
                    time.time(),
                ),
            )
            self.conn.commit()
            task_id = cursor.lastrowid
        return task_id

    def schedule_task(
        self, func: Union[Callable, str], run_at: datetime, *args, **kwargs
    ) -> int:
        """Schedule a task to run at a specific time."""
        kwargs["_scheduled_time"] = run_at.timestamp()
        return self.add_task(func, *args, **kwargs)

    def get_next_task(self) -> Optional[sqlite3.Row]:
        """Get the next pending task that is ready to run."""
        current_time = time.time()
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT * FROM tasks 
                WHERE status = ? 
                AND (scheduled_time IS NULL OR scheduled_time <= ?)
                ORDER BY scheduled_time IS NULL DESC, scheduled_time ASC, created_time ASC
                LIMIT 1
            """,
                (TaskStatus.PENDING.value, current_time),
            )
            return cursor.fetchone()

    def update_task_status(
        self, task_id: int, status: TaskStatus, result: Any = None, error: str = None
    ):
        """Update task status and optionally store result or error."""
        # Serialize result if needed
        serialized_result = None
        if result is not None:
            try:
                serialized_result = json.dumps(result)
                serialization_method = SerializationMethod.JSON.value
            except (TypeError, ValueError):
                serialized_result = pickle.dumps(result)
                serialization_method = SerializationMethod.PICKLE.value
        else:
            serialization_method = None

        with self.lock:
            cursor = self.conn.cursor()
            completed_time = (
                time.time()
                if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
                else None
            )
            cursor.execute(
                """
                UPDATE tasks 
                SET status = ?, result = ?, error = ?, completed_time = ?
                WHERE id = ?
            """,
                (status.value, serialized_result, error, completed_time, task_id),
            )
            self.conn.commit()

    def get_task_result(self, task_id: int) -> Any:
        """Retrieve and deserialize task result."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT result, serialization_method FROM tasks WHERE id = ?",
                (task_id,),
            )
            row = cursor.fetchone()
            if not row or row["result"] is None:
                return None

            if row["serialization_method"] == SerializationMethod.JSON.value:
                return json.loads(row["result"])
            else:
                return pickle.loads(row["result"])

    def start_worker(self, task_registry: dict, sleep_interval: float = 1.0):
        """Start a background worker thread to process tasks."""
        if self._running:
            return

        self._running = True
        self._worker_thread = threading.Thread(
            target=self._worker_loop, args=(task_registry, sleep_interval), daemon=True
        )
        self._worker_thread.start()

    def stop_worker(self):
        """Stop the background worker thread."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join()

    def _worker_loop(self, task_registry: dict, sleep_interval: float):
        """Main worker loop that processes tasks."""
        while self._running:
            task = self.get_next_task()
            if task:
                self._process_task(task, task_registry)
            else:
                time.sleep(sleep_interval)

    def _process_task(self, task: sqlite3.Row, task_registry: dict):
        """Process a single task."""
        task_id = task["id"]
        func_name = task["func"]
        serialization_method = task["serialization_method"]

        # Deserialize arguments
        if serialization_method == SerializationMethod.JSON.value:
            args = tuple(json.loads(task["args"])) if task["args"] else ()
            kwargs = json.loads(task["kwargs"]) if task["kwargs"] else {}
        else:
            args = pickle.loads(task["args"]) if task["args"] else ()
            kwargs = pickle.loads(task["kwargs"]) if task["kwargs"] else {}

        # Update status to running
        self.update_task_status(task_id, TaskStatus.RUNNING)

        try:
            # Execute task
            if func_name not in task_registry:
                raise ValueError(f"Function '{func_name}' not registered")

            func = task_registry[func_name]
            result = func(*args, **kwargs)
            self.update_task_status(task_id, TaskStatus.COMPLETED, result=result)
        except Exception as e:
            self.update_task_status(task_id, TaskStatus.FAILED, error=str(e))

    def get_task_status(self, task_id: int) -> TaskStatus:
        """Get the current status of a task."""
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Task with ID {task_id} not found")
            return TaskStatus(row["status"])

    def close(self):
        """Close the database connection."""
        self.conn.close()


# Example usage
if __name__ == "__main__":
    # Define some test functions
    def add_numbers(a, b):
        return a + b

    def multiply_numbers(a, b):
        return a * b

    def fail_task():
        raise Exception("This task always fails")

    # Create task queue
    queue = TaskQueue("example_queue.db")

    # Register functions
    tasks = {
        "add_numbers": add_numbers,
        "multiply_numbers": multiply_numbers,
        "fail_task": fail_task,
    }

    # Add tasks
    task1_id = queue.add_task("add_numbers", 5, 3)
    task2_id = queue.add_task("multiply_numbers", 4, 7)
    task3_id = queue.add_task("fail_task")

    # Schedule a future task
    future_time = datetime.fromtimestamp(time.time() + 5)  # 5 seconds from now
    task4_id = queue.schedule_task("add_numbers", future_time, 10, 20)

    print(f"Added tasks with IDs: {task1_id}, {task2_id}, {task3_id}, {task4_id}")

    # Start worker
    queue.start_worker(tasks, sleep_interval=0.5)

    # Wait for tasks to complete
    time.sleep(10)

    # Check results
    print(f"Task 1 result: {queue.get_task_result(task1_id)}")
    print(f"Task 2 result: {queue.get_task_result(task2_id)}")
    print(f"Task 3 status: {queue.get_task_status(task3_id)}")
    print(f"Task 4 result: {queue.get_task_result(task4_id)}")

    # Clean up
    queue.close()
