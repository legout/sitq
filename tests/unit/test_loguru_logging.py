"""Test logging behavior with loguru replacement."""

import tempfile
import threading
import time
from io import StringIO

from src.sitq.backends.sqlite import SQLiteBackend
from src.sitq.worker import Worker


def test_worker_logging_output():
    """Test that worker logging works with loguru and produces expected output."""
    # Create backend
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        backend = SQLiteBackend(tmp.name)

        # Capture log output
        log_capture = StringIO()

        # Import loguru and add capture handler
        from loguru import logger

        logger.remove()  # Remove default handler
        logger.add(
            log_capture,
            level="DEBUG",
            format="{time} | {level} | {name}:{function}:{line} - {message}",
        )

        # Create worker
        worker = Worker(backend, max_concurrency=1, poll_interval=0.1)

        def run_worker():
            import asyncio

            asyncio.run(worker.start())

        # Start worker in background
        worker_thread = threading.Thread(target=run_worker, daemon=True)
        worker_thread.start()

        try:
            # Give worker time to start
            time.sleep(0.5)

            # Stop worker to trigger lifecycle logging
            import asyncio

            stop_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(stop_loop)
            try:
                stop_loop.run_until_complete(worker.stop())
            finally:
                stop_loop.close()

            worker_thread.join(timeout=5.0)

            # Check captured log output
            log_output = log_capture.getvalue()

            # Verify expected log messages are present
            assert "Starting worker with" in log_output
            assert "Worker stopped gracefully" in log_output
            assert (
                "Worker stopped" in log_output
                or "Worker stopped gracefully" in log_output
            )

            print("✓ Worker logging test passed!")
            print(f"Log output captured:\n{log_output}")

        finally:
            # Restore default logger configuration
            logger.remove()
            logger.add(lambda msg: print(msg, end=""))  # Default console output


def test_logging_levels():
    """Test that different log levels work correctly."""
    from loguru import logger

    # Capture log output
    log_capture = StringIO()
    logger.remove()  # Remove default handler
    logger.add(log_capture, level="DEBUG", format="{level} | {message}")

    # Test different log levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    # Check output
    log_output = log_capture.getvalue()

    # Verify all levels are present
    assert "DEBUG" in log_output
    assert "INFO" in log_output
    assert "WARNING" in log_output
    assert "ERROR" in log_output

    print("✓ Logging levels test passed!")
    print(f"Log output captured:\n{log_output}")

    # Restore default logger
    logger.remove()
    logger.add(lambda msg: print(msg, end=""))


if __name__ == "__main__":
    print("Testing loguru logging behavior...")
    test_logging_levels()
    print()
    test_worker_logging_output()
    print("All logging tests completed!")
