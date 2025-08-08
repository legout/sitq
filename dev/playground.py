import marimo

__generated_with = "0.14.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from sitq import (
        TaskQueue,
        SyncTaskQueue,
        SQLiteBackend,
        PickleSerializer,
        AsyncWorker,
        ThreadWorker,
        ProcessWorker,
    )

    import asyncio
    import aiohttp
    import time
    import random
    from loguru import logger
    from typing import Dict, Any, List
    return (
        Any,
        AsyncWorker,
        Dict,
        List,
        PickleSerializer,
        SQLiteBackend,
        TaskQueue,
        asyncio,
        logger,
        random,
        time,
    )


@app.cell(hide_code=True)
def _(Any, Dict, List, logger, random, time):
    def slow_calculation_task(n: int) -> Dict[str, Any]:
        """A task that performs a slow calculation"""
        # Simulate some work
        logger.info(f"Starting slow calculation task with input: {n}")
        start_time = time.time()
        time.sleep(0.1)

        result = sum(i**2 for i in range(n))
        duration = time.time() - start_time

        logger.info(
            f"Completed slow calculation task. Input: {n}, Result: {result}, Duration: {duration:.2f}s"
        )
        return {
            "task_type": "slow_calculation",
            "input": n,
            "result": result,
            "duration": 0.1,
        }


    def data_processing_task(data: List[float]) -> Dict[str, Any]:
        """A task that processes a list of numbers"""
        logger.info(f"Starting data processing task with input size: {len(data)}")
        # Simulate some processing
        start_time = time.time()
        time.sleep(0.05)

        if not data:
            return {"task_type": "data_processing", "error": "Empty data list"}

        processed_data = [x * 2 + 1 for x in data]
        duration = time.time() - start_time
        logger.info(
            f"Completed data processing task. Input size: {len(data)}, Duration: {duration:.2f}s"
        )
        return {
            "task_type": "data_processing",
            "input_size": len(data),
            "processed_data": processed_data,
            "average": sum(processed_data) / len(processed_data),
            "duration": 0.05,
        }


    def api_call_task(url: str, timeout: float = 1.0) -> Dict[str, Any]:
        """A task that simulates an API call"""
        logger.info(f"Starting API call task for URL: {url}")
        start_time = time.time()
        # Simulate network delay
        time.sleep(timeout)

        # Simulate different responses
        success_rate = random.random()
        duration = time.time() - start_time
        logger.info(
            f"Completed API call task for URL: {url}, Success Rate: {success_rate:.2f}, Duration: {duration:.2f}s"
        )

        if success_rate > 0.2:  # 80% success rate
            return {
                "task_type": "api_call",
                "url": url,
                "status": "success",
                "response_time": timeout,
                "data": {"message": f"Data from {url}", "timestamp": time.time()},
            }
        else:
            return {
                "task_type": "api_call",
                "url": url,
                "status": "error",
                "error": "Connection timeout",
                "response_time": timeout,
            }


    def file_operation_task(filename: str, operation: str) -> Dict[str, Any]:
        """A task that simulates file operations"""
        logger.info(f"Starting file operation task: {operation} on {filename}")
        start_time = time.time()
        time.sleep(0.02)
        duration = time.time() - start_time
        logger.info(
            f"Completed file operation task: {operation} on {filename}, Duration: {duration:.2f}s"
        )
        if operation == "read":
            return {
                "task_type": "file_operation",
                "filename": filename,
                "operation": "read",
                "content": f"Content of {filename}",
                "size": len(f"Content of {filename}"),
                "duration": 0.02,
            }
        elif operation == "write":
            return {
                "task_type": "file_operation",
                "filename": filename,
                "operation": "write",
                "status": "success",
                "written_bytes": 1024,
                "duration": 0.02,
            }
        else:
            return {
                "task_type": "file_operation",
                "filename": filename,
                "operation": operation,
                "error": f"Unsupported operation: {operation}",
            }
    return


@app.cell(hide_code=True)
def _(Any, Dict, List, asyncio, logger, random, time):
    async def async_slow_calculation_task(n: int) -> Dict[str, Any]:
        """An async task that performs a slow calculation"""
        logger.info(f"Starting async slow calculation task with input: {n}")

        # Simulate some work asynchronously
        start_time = time.time()
        await asyncio.sleep(0.1)

        result = sum(i**2 for i in range(n))
        duration = time.time() - start_time

        logger.success(
            f"Completed async slow calculation task. Input: {n}, Result: {result}, Duration: {duration:.2f}s"
        )

        return {
            "task_type": "async_slow_calculation",
            "input": n,
            "result": result,
            "duration": duration,
        }


    async def async_data_processing_task(data: List[float]) -> Dict[str, Any]:
        """An async task that processes a list of numbers"""
        logger.info(
            f"Starting async data processing task with input size: {len(data)}"
        )

        start_time = time.time()
        await asyncio.sleep(0.05)

        if not data:
            logger.error("Async data processing task failed: Empty data list")
            return {
                "task_type": "async_data_processing",
                "error": "Empty data list",
            }

        processed_data = [x * 2 + 1 for x in data]
        duration = time.time() - start_time

        average = sum(processed_data) / len(processed_data)
        logger.success(
            f"Completed async data processing task. Input size: {len(data)}, Average: {average:.2f}, Duration: {duration:.2f}s"
        )

        return {
            "task_type": "async_data_processing",
            "input_size": len(data),
            "processed_data": processed_data,
            "average": average,
            "duration": duration,
        }


    async def async_api_call_task(
        url: str, timeout: float = 1.0
    ) -> Dict[str, Any]:
        """An async task that simulates an API call"""
        logger.info(f"Starting async API call task for URL: {url}")

        # Simulate network delay asynchronously
        start_time = time.time()
        await asyncio.sleep(timeout)

        # Simulate different responses
        success_rate = random.random()
        duration = time.time() - start_time

        if success_rate > 0.2:  # 80% success rate
            logger.success(
                f"Completed async API call task for URL: {url}. Status: success, Response time: {duration:.2f}s"
            )
            return {
                "task_type": "async_api_call",
                "url": url,
                "status": "success",
                "response_time": duration,
                "data": {"message": f"Data from {url}", "timestamp": time.time()},
            }
        else:
            logger.warning(
                f"Async API call task for URL: {url} failed. Status: error, Error: Connection timeout, Response time: {duration:.2f}s"
            )
            return {
                "task_type": "async_api_call",
                "url": url,
                "status": "error",
                "error": "Connection timeout",
                "response_time": duration,
            }


    async def async_file_operation_task(
        filename: str, operation: str
    ) -> Dict[str, Any]:
        """An async task that simulates file operations"""
        logger.info(
            f"Starting async file operation task: {operation} on {filename}"
        )

        start_time = time.time()
        await asyncio.sleep(0.02)
        duration = time.time() - start_time

        if operation == "read":
            content = f"Content of {filename}"
            logger.success(
                f"Completed async file read operation. Filename: {filename}, Size: {len(content)} bytes, Duration: {duration:.2f}s"
            )
            return {
                "task_type": "async_file_operation",
                "filename": filename,
                "operation": "read",
                "content": content,
                "size": len(content),
                "duration": duration,
            }
        elif operation == "write":
            logger.success(
                f"Completed async file write operation. Filename: {filename}, Written bytes: 1024, Duration: {duration:.2f}s"
            )
            return {
                "task_type": "async_file_operation",
                "filename": filename,
                "operation": "write",
                "status": "success",
                "written_bytes": 1024,
                "duration": duration,
            }
        else:
            logger.error(
                f"Async file operation task failed: Unsupported operation '{operation}' on {filename}"
            )
            return {
                "task_type": "async_file_operation",
                "filename": filename,
                "operation": operation,
                "error": f"Unsupported operation: {operation}",
            }
    return


@app.cell
async def _(PickleSerializer, SQLiteBackend, TaskQueue):
    queue = TaskQueue(
        backend=SQLiteBackend("sqlite+aiosqlite:///pytaskqueue.db"),
        serializer=PickleSerializer(),
    )

    await queue.backend.connect()
    return (queue,)


@app.function
async def say_hello(name: str):
    print(f"Hello, {name}")
    return f"Greetings, {name}!"


@app.cell
async def _(queue):
    task_id = await queue.enqueue(say_hello, "World")
    print(f"Task {task_id} enqueued.")
    return (task_id,)


@app.cell
async def _(AsyncWorker, PickleSerializer, asyncio, queue):
    worker = AsyncWorker(
            backend=queue.backend,
            serializer=PickleSerializer(),
            concurrency=5
        )

    # Run the worker for a short period to process the task
    await worker.start()
    await asyncio.sleep(1) # Allow time for the task to be processed
    await worker.stop()
    return


@app.cell
async def _(queue, task_id):
    result = await queue.get_result(task_id, timeout=5)
    return


@app.cell
def _(queue):
    queue.backend.close()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
