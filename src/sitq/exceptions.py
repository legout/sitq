"""Domain-specific exception hierarchy for sitq.

This module defines the exception hierarchy used throughout sitq to provide
consistent error handling, proper context, and actionable error messages.
"""

from __future__ import annotations

__all__ = [
    "SitqError",
    "TaskQueueError",
    "BackendError",
    "WorkerError",
    "ValidationError",
    "SerializationError",
    "ConnectionError",
    "TaskExecutionError",
    "TimeoutError",
    "ResourceExhaustionError",
    "ConfigurationError",
    "SyncTaskQueueError",
]

from typing import Optional, Any, Dict
from datetime import datetime


class SitqError(Exception):
    """Base exception for all sitq-related errors.

    All sitq exceptions inherit from this base class to allow
    for catch-all error handling while maintaining specific error types.
    """

    def __init__(
        self,
        message: str,
        *,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize sitq error with message and optional context.

        Args:
            message: Human-readable error message.
            cause: Original exception that caused this error.
            context: Additional context information for debugging.
        """
        super().__init__(message)
        self.message = message
        self.cause = cause
        self.context = context or {}

        # Set cause for exception chaining
        if cause:
            self.__cause__ = cause

    def __str__(self) -> str:
        """Return string representation with context."""
        base_msg = self.message
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base_msg += f" (context: {context_str})"
        return base_msg


class TaskQueueError(SitqError):
    """Base exception for task queue operations."""

    def __init__(
        self,
        message: str,
        *,
        task_id: Optional[str] = None,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize task queue error.

        Args:
            message: Human-readable error message.
            task_id: ID of the related task, if applicable.
            cause: Original exception that caused this error.
            context: Additional context information.
        """
        context = context or {}
        if task_id:
            context["task_id"] = task_id

        super().__init__(message, cause=cause, context=context)
        self.task_id = task_id


class BackendError(SitqError):
    """Base exception for backend operations."""

    def __init__(
        self,
        message: str,
        *,
        operation: Optional[str] = None,
        backend_type: Optional[str] = None,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize backend error.

        Args:
            message: Human-readable error message.
            operation: Backend operation that failed (e.g., "enqueue", "reserve").
            backend_type: Type of backend (e.g., "sqlite", "postgres").
            cause: Original exception that caused this error.
            context: Additional context information.
        """
        context = context or {}
        if operation:
            context["operation"] = operation
        if backend_type:
            context["backend_type"] = backend_type

        super().__init__(message, cause=cause, context=context)
        self.operation = operation
        self.backend_type = backend_type


class WorkerError(SitqError):
    """Base exception for worker operations."""

    def __init__(
        self,
        message: str,
        *,
        task_id: Optional[str] = None,
        worker_id: Optional[str] = None,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize worker error.

        Args:
            message: Human-readable error message.
            task_id: ID of the task being processed.
            worker_id: ID of the worker, if applicable.
            cause: Original exception that caused this error.
            context: Additional context information.
        """
        context = context or {}
        if task_id:
            context["task_id"] = task_id
        if worker_id:
            context["worker_id"] = worker_id

        super().__init__(message, cause=cause, context=context)
        self.task_id = task_id
        self.worker_id = worker_id


# Specific exception types for common scenarios


class ValidationError(SitqError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        *,
        parameter: Optional[str] = None,
        value: Optional[Any] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Human-readable error message.
            parameter: Name of the parameter that failed validation.
            value: The invalid value (if safe to include).
            cause: Original exception that caused this error.
        """
        context = {}
        if parameter:
            context["parameter"] = parameter
        if value is not None:
            context["value"] = str(value)

        super().__init__(message, cause=cause, context=context)
        self.parameter = parameter
        self.value = value


class SerializationError(SitqError):
    """Raised when serialization/deserialization fails."""

    def __init__(
        self,
        message: str,
        *,
        operation: Optional[str] = None,
        data_type: Optional[str] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize serialization error.

        Args:
            message: Human-readable error message.
            operation: Operation that failed ("serialize" or "deserialize").
            data_type: Type of data being processed.
            cause: Original exception that caused this error.
        """
        context = {}
        if operation:
            context["operation"] = operation
        if data_type:
            context["data_type"] = data_type

        super().__init__(message, cause=cause, context=context)
        self.operation = operation
        self.data_type = data_type


class ConnectionError(BackendError):
    """Raised when backend connection fails."""

    def __init__(
        self,
        message: str,
        *,
        backend_type: Optional[str] = None,
        connection_details: Optional[str] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize connection error.

        Args:
            message: Human-readable error message.
            backend_type: Type of backend.
            connection_details: Additional connection information.
            cause: Original exception that caused this error.
        """
        context = {}
        if connection_details:
            context["connection_details"] = connection_details

        super().__init__(
            message,
            operation="connect",
            backend_type=backend_type,
            cause=cause,
            context=context,
        )
        self.connection_details = connection_details


class TaskExecutionError(WorkerError):
    """Raised when task execution fails."""

    def __init__(
        self,
        message: str,
        *,
        task_id: Optional[str] = None,
        function_name: Optional[str] = None,
        execution_time: Optional[float] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize task execution error.

        Args:
            message: Human-readable error message.
            task_id: ID of the failed task.
            function_name: Name of the function that failed.
            execution_time: Time taken before failure (seconds).
            cause: Original exception that caused this error.
        """
        context = {}
        if function_name:
            context["function_name"] = function_name
        if execution_time is not None:
            context["execution_time"] = execution_time

        super().__init__(message, task_id=task_id, cause=cause, context=context)
        self.function_name = function_name
        self.execution_time = execution_time


class TimeoutError(TaskQueueError):
    """Raised when operations timeout."""

    def __init__(
        self,
        message: str,
        *,
        task_id: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize timeout error.

        Args:
            message: Human-readable error message.
            task_id: ID of the task that timed out.
            timeout_seconds: Timeout duration in seconds.
            operation: Operation that timed out.
            cause: Original exception that caused this error.
        """
        context = {}
        if timeout_seconds is not None:
            context["timeout_seconds"] = timeout_seconds
        if operation:
            context["operation"] = operation

        super().__init__(message, task_id=task_id, cause=cause, context=context)
        self.timeout_seconds = timeout_seconds
        self.operation = operation


class ResourceExhaustionError(SitqError):
    """Raised when system resources are exhausted."""

    def __init__(
        self,
        message: str,
        *,
        resource_type: Optional[str] = None,
        current_usage: Optional[Any] = None,
        limit: Optional[Any] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize resource exhaustion error.

        Args:
            message: Human-readable error message.
            resource_type: Type of resource (memory, connections, etc.).
            current_usage: Current resource usage.
            limit: Resource limit that was exceeded.
            cause: Original exception that caused this error.
        """
        context = {}
        if resource_type:
            context["resource_type"] = resource_type
        if current_usage is not None:
            context["current_usage"] = str(current_usage)
        if limit is not None:
            context["limit"] = str(limit)

        super().__init__(message, cause=cause, context=context)
        self.resource_type = resource_type
        self.current_usage = current_usage
        self.limit = limit


class SyncTaskQueueError(TaskQueueError):
    """Raised when SyncTaskQueue operations fail."""

    def __init__(
        self,
        message: str,
        *,
        task_id: Optional[str] = None,
        operation: Optional[str] = None,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize sync task queue error.

        Args:
            message: Human-readable error message.
            task_id: ID of the related task, if applicable.
            operation: Operation that failed (e.g., "enqueue", "get_result").
            cause: Original exception that caused this error.
            context: Additional context information.
        """
        context = context or {}
        if operation:
            context["operation"] = operation

        super().__init__(message, task_id=task_id, cause=cause, context=context)
        self.operation = operation


class ConfigurationError(SitqError):
    """Raised when configuration is invalid."""

    def __init__(
        self,
        message: str,
        *,
        parameter: Optional[str] = None,
        value: Optional[Any] = None,
        valid_options: Optional[list] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize configuration error.

        Args:
            message: Human-readable error message.
            parameter: Configuration parameter that is invalid.
            value: The invalid configuration value.
            valid_options: List of valid options, if applicable.
            cause: Original exception that caused this error.
        """
        context = {}
        if parameter:
            context["parameter"] = parameter
        if value is not None:
            context["value"] = str(value)
        if valid_options:
            context["valid_options"] = valid_options

        super().__init__(message, cause=cause, context=context)
        self.parameter = parameter
        self.value = value
        self.valid_options = valid_options
