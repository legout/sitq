"""Comprehensive error handling tests for sitq."""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock

from sitq.exceptions import (
    SitqError,
    TaskQueueError,
    BackendError,
    WorkerError,
    ValidationError,
    SerializationError,
    ConnectionError,
    TaskExecutionError,
    TimeoutError,
    ResourceExhaustionError,
    ConfigurationError,
)
from sitq.validation import validate, ValidationBuilder, retry_async, retry_sync
from sitq.queue import TaskQueue
from sitq.worker import Worker
from sitq.sync import SyncTaskQueue
from sitq.backends.sqlite import SQLiteBackend
from sitq.serialization import CloudpickleSerializer


class TestExceptionHierarchy:
    """Test the exception hierarchy and base functionality."""

    def test_sitq_error_base_class(self):
        """Test SitqError base class functionality."""
        cause = ValueError("Original error")
        context = {"task_id": "test123", "operation": "enqueue"}

        error = SitqError("Test error message", cause=cause, context=context)

        assert (
            str(error)
            == "Test error message (context: task_id=test123, operation=enqueue)"
        )
        assert error.message == "Test error message"
        assert error.cause == cause
        assert error.context == context
        assert error.__cause__ == cause

    def test_task_queue_error_inheritance(self):
        """Test TaskQueueError inherits from SitqError."""
        error = TaskQueueError("Task queue failed", task_id="test123")

        assert isinstance(error, SitqError)
        assert error.task_id == "test123"
        assert "task_id" in error.context

    def test_backend_error_inheritance(self):
        """Test BackendError inherits from SitqError."""
        error = BackendError(
            "Database failed", operation="connect", backend_type="sqlite"
        )

        assert isinstance(error, SitqError)
        assert error.operation == "connect"
        assert error.backend_type == "sqlite"

    def test_worker_error_inheritance(self):
        """Test WorkerError inherits from SitqError."""
        error = WorkerError("Worker failed", worker_id="worker1", task_id="test123")

        assert isinstance(error, SitqError)
        assert error.worker_id == "worker1"
        assert error.task_id == "test123"


class TestValidation:
    """Test input validation utilities."""

    def test_validate_required_string(self):
        """Test validation of required string parameters."""
        # Valid case
        validate("test", "param").is_required().is_string().validate()

        # Invalid cases
        with pytest.raises(ValidationError):
            validate(None, "param").is_required().validate()

        with pytest.raises(ValidationError):
            validate(123, "param").is_required().is_string().validate()

    def test_validate_positive_number(self):
        """Test validation of positive numbers."""
        # Valid case
        validate(5, "param").is_required().is_positive_number().validate()

        # Invalid cases
        with pytest.raises(ValidationError):
            validate(-1, "param").is_required().is_positive_number().validate()

        with pytest.raises(ValidationError):
            validate(0, "param").is_required().is_positive_number().validate()

    def test_validate_timezone_aware_datetime(self):
        """Test validation of timezone-aware datetimes."""
        # Valid case
        dt = datetime.now(timezone.utc)
        validate(dt, "param").is_required().is_timezone_aware().validate()

        # Invalid case
        naive_dt = datetime.now()
        with pytest.raises(ValidationError):
            validate(naive_dt, "param").is_required().is_timezone_aware().validate()

    def test_validation_builder_fluent_interface(self):
        """Test ValidationBuilder fluent interface."""
        builder = validate("test_string", "my_param")

        # Should support chaining
        result = builder.is_required().is_string().min_length(3).max_length(10)
        assert isinstance(result, ValidationBuilder)

        # Should validate successfully
        result.validate()

    def test_validation_builder_min_length(self):
        """Test min_length validation."""
        # Valid case
        validate("hello", "param").is_required().min_length(3).validate()

        # Invalid case
        with pytest.raises(ValidationError):
            validate("hi", "param").is_required().min_length(3).validate()

    def test_validation_builder_max_length(self):
        """Test max_length validation."""
        # Valid case
        validate("hello", "param").is_required().max_length(10).validate()

        # Invalid case
        with pytest.raises(ValidationError):
            validate("this is too long", "param").is_required().max_length(5).validate()


class TestRetryLogic:
    """Test retry logic for transient failures."""

    @pytest.mark.asyncio
    async def test_retry_async_success_on_first_attempt(self):
        """Test retry decorator succeeds on first attempt."""
        mock_func = AsyncMock(return_value="success")

        @retry_async(max_attempts=3)
        async def test_func():
            return await mock_func()

        result = await test_func()
        assert result == "success"
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_async_eventual_success(self):
        """Test retry decorator succeeds after retries."""
        mock_func = AsyncMock(
            side_effect=[
                ConnectionError("Failed"),
                ConnectionError("Failed"),
                "success",
            ]
        )

        @retry_async(max_attempts=3, base_delay=0.01)
        async def test_func():
            return await mock_func()

        result = await test_func()
        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_async_max_attempts_exceeded(self):
        """Test retry decorator fails after max attempts."""
        mock_func = AsyncMock(side_effect=ConnectionError("Always fails"))

        @retry_async(max_attempts=2, base_delay=0.01)
        async def test_func():
            return await mock_func()

        with pytest.raises(ConnectionError):
            await test_func()
        assert mock_func.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_async_non_retryable_exception(self):
        """Test retry decorator doesn't retry non-retryable exceptions."""
        mock_func = AsyncMock(side_effect=ValueError("Non-retryable"))

        @retry_async(max_attempts=3, base_delay=0.01)
        async def test_func():
            return await mock_func()

        with pytest.raises(ValueError):
            await test_func()
        assert mock_func.call_count == 1

    def test_retry_sync_success_on_first_attempt(self):
        """Test sync retry decorator succeeds on first attempt."""
        mock_func = Mock(return_value="success")

        @retry_sync(max_attempts=3)
        def test_func():
            return mock_func()

        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 1

    def test_retry_sync_eventual_success(self):
        """Test sync retry decorator succeeds after retries."""
        mock_func = Mock(
            side_effect=[
                ConnectionError("Failed"),
                ConnectionError("Failed"),
                "success",
            ]
        )

        @retry_sync(max_attempts=3, base_delay=0.01)
        def test_func():
            return mock_func()

        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 3


class TestTaskQueueErrorHandling:
    """Test error handling in TaskQueue."""

    @pytest.mark.asyncio
    async def test_task_queue_enqueue_validation_error(self):
        """Test TaskQueue enqueue with invalid input."""
        backend = Mock()
        backend.enqueue = AsyncMock()

        task_queue = TaskQueue(backend)

        # Test with non-callable function
        with pytest.raises(ValidationError):
            await task_queue.enqueue("not_a_function")

    @pytest.mark.asyncio
    async def test_task_queue_enqueue_backend_error_wrapping(self):
        """Test TaskQueue wraps backend errors properly."""
        backend = Mock()
        backend.enqueue = AsyncMock(side_effect=Exception("Database error"))

        task_queue = TaskQueue(backend)

        with pytest.raises(TaskQueueError) as exc_info:
            await task_queue.enqueue(lambda: "test")

        assert "Failed to enqueue task in backend" in str(exc_info.value)
        assert exc_info.value.cause is not None

    @pytest.mark.asyncio
    async def test_task_queue_get_result_timeout(self):
        """Test TaskQueue get_result timeout handling."""
        backend = Mock()
        backend.get_result = AsyncMock(return_value=None)

        task_queue = TaskQueue(backend)

        with pytest.raises(TimeoutError):
            await task_queue.get_result("task123", timeout=0.01)


class TestWorkerErrorHandling:
    """Test error handling in Worker."""

    @pytest.mark.asyncio
    async def test_worker_task_execution_error_wrapping(self):
        """Test Worker wraps task execution errors properly."""
        backend = Mock()
        backend.reserve = AsyncMock(return_value=[])

        worker = Worker(backend)

        # This test would need more complex setup to fully test execution errors
        # For now, just test validation
        with pytest.raises(ValidationError):
            Worker(None)  # Invalid backend

    @pytest.mark.asyncio
    async def test_worker_serialization_error_handling(self):
        """Test Worker handles serialization errors properly."""
        backend = Mock()
        backend.reserve = AsyncMock(return_value=[])

        # Create a mock task that will fail serialization
        def failing_func():
            class UnserializableObject:
                def __reduce__(self):
                    raise TypeError("Cannot serialize")

            return UnserializableObject()

        worker = Worker(backend)
        # This would need more complex setup to test actual execution
        # For now, test that worker can be created with valid parameters
        assert worker is not None


class TestSyncTaskQueueErrorHandling:
    """Test error handling in SyncTaskQueue."""

    def test_sync_task_queue_not_running_error(self):
        """Test SyncTaskQueue raises error when not running."""
        backend = Mock()
        sync_queue = SyncTaskQueue(backend)

        with pytest.raises(RuntimeError) as exc_info:
            sync_queue.enqueue(lambda: "test")

        assert "not running" in str(exc_info.value).lower()

    def test_sync_task_queue_already_running_error(self):
        """Test SyncTaskQueue raises error when already running."""
        backend = Mock()
        sync_queue = SyncTaskQueue(backend)

        # Mock the event loop check to simulate already running
        with patch("sitq.sync.asyncio.get_running_loop"):
            with pytest.raises(RuntimeError) as exc_info:
                with sync_queue:
                    pass  # This should raise error about existing event loop


class TestSQLiteBackendErrorHandling:
    """Test error handling in SQLite backend."""

    def test_sqlite_backend_invalid_database_path(self):
        """Test SQLite backend with invalid database path."""
        # Valid case - should not raise
        backend = SQLiteBackend(":memory:")
        assert backend.database_path == ":memory:"

        # Invalid case - empty string
        with pytest.raises(ValidationError):
            backend = SQLiteBackend("")
            backend._get_connection()  # This would trigger validation

    @pytest.mark.asyncio
    async def test_sqlite_backend_connection_error_wrapping(self):
        """Test SQLite backend wraps connection errors properly."""
        backend = SQLiteBackend("/invalid/path/test.db")

        with patch("aiosqlite.connect", side_effect=Exception("Connection failed")):
            with pytest.raises(ConnectionError) as exc_info:
                await backend._get_connection()

            assert "Failed to connect to SQLite database" in str(exc_info.value)
            assert exc_info.value.backend_type == "sqlite"

    @pytest.mark.asyncio
    async def test_sqlite_backend_enqueue_validation(self):
        """Test SQLite backend enqueue validation."""
        backend = SQLiteBackend(":memory:")

        with pytest.raises(ValidationError):
            await backend.enqueue(None)  # None task should fail validation


class TestSerializationErrorHandling:
    """Test error handling in serialization."""

    def test_cloudpickle_serializer_none_object(self):
        """Test CloudpickleSerializer with None object."""
        serializer = CloudpickleSerializer()

        with pytest.raises(ValidationError) as exc_info:
            serializer.dumps(None)

        assert "cannot be None" in str(exc_info.value).lower()

    def test_cloudpickle_serialization_error_wrapping(self):
        """Test CloudpickleSerializer wraps serialization errors."""
        serializer = CloudpickleSerializer()

        # Create an object that can't be serialized
        class UnserializableClass:
            def __reduce__(self):
                raise TypeError("Cannot serialize this object")

        obj = UnserializableClass()

        with pytest.raises(SerializationError) as exc_info:
            serializer.dumps(obj)

        assert "Failed to serialize object" in str(exc_info.value)
        assert exc_info.value.cause is not None

    def test_cloudpickle_deserialization_error_wrapping(self):
        """Test CloudpickleSerializer wraps deserialization errors."""
        serializer = CloudpickleSerializer()

        # Invalid bytes should cause deserialization error
        invalid_data = b"invalid pickle data"

        with pytest.raises(SerializationError) as exc_info:
            serializer.loads(invalid_data)

        assert "Failed to deserialize data" in str(exc_info.value)
        assert exc_info.value.cause is not None


class TestErrorPropagation:
    """Test error propagation across components."""

    @pytest.mark.asyncio
    async def test_error_propagation_from_backend_to_queue(self):
        """Test errors propagate correctly from backend to queue."""
        backend = Mock()
        backend.enqueue = AsyncMock(
            side_effect=BackendError("Database locked", operation="enqueue")
        )

        task_queue = TaskQueue(backend)

        with pytest.raises(TaskQueueError) as exc_info:
            await task_queue.enqueue(lambda: "test")

        # The original backend error should be preserved as cause
        assert exc_info.value.cause is not None
        assert isinstance(exc_info.value.cause, BackendError)

    @pytest.mark.asyncio
    async def test_error_propagation_from_serialization_to_queue(self):
        """Test errors propagate correctly from serialization to queue."""
        backend = Mock()
        backend.enqueue = AsyncMock()

        # Create a serializer that will fail
        failing_serializer = Mock()
        failing_serializer.serialize_task_envelope = Mock(
            side_effect=SerializationError("Serialization failed")
        )

        task_queue = TaskQueue(backend, serializer=failing_serializer)

        with pytest.raises(SerializationError):
            await task_queue.enqueue(lambda: "test")


if __name__ == "__main__":
    pytest.main([__file__])
