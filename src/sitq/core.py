"""Core data models for sitq."""

from __future__ import annotations

__all__ = ["Task", "Result", "ReservedTask", "_now"]

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any


@dataclass
class Result:
    """Result of a finished task execution.

    Attributes:
        id: Unique identifier for this result record.
        task_id: ID of the task this result belongs to.
        status: Execution status - "success", "failed", or "pending".
        value: Serialized return value from successful task execution.
        error: Human-readable error message for failed tasks.
        traceback: Formatted stack trace for failed tasks.
        enqueued_at: UTC timestamp when task was enqueued.
        started_at: UTC timestamp when task execution began.
        finished_at: UTC timestamp when task completed (success or failure).

    Example:
        >>> result = Result(
        ...     task_id="abc123",
        ...     status="success",
        ...     value=b'"Hello, World!"',
        ...     enqueued_at=datetime.now(timezone.utc)
        ... )
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    status: str = "pending"  # "success", "failed"
    value: Optional[bytes] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    enqueued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


@dataclass
class Task:
    """A unit of work that the queue will execute.

    Attributes:
        id: Unique identifier for this task.
        func: Serialized callable envelope containing function and arguments.
        args: Legacy field - not used in current implementation.
        kwargs: Legacy field - not used in current implementation.
        context: Serialized contextvars.Context for task execution.
        schedule: Optional scheduling configuration for recurring tasks.
        created_at: UTC timestamp when task was created.
        available_at: UTC timestamp when task becomes eligible for execution.
        last_run_time: UTC timestamp of most recent execution attempt.
        result_id: Reference to result record when task completes.

    Retry and locking attributes:
        retries: Number of times this task has been attempted.
        max_retries: Maximum number of retry attempts allowed.
        retry_backoff: Backoff multiplier for retry delays.
        lock_id: Identifier of worker currently processing this task.
        locked_until: UTC timestamp when worker lock expires.

    Example:
        >>> task = Task(
        ...     func=serialized_function,
        ...     available_at=datetime.now(timezone.utc)
        ... )
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    func: bytes = b""  # Serialized callable envelope
    args: Optional[bytes] = None  # Not used - envelope contains args
    kwargs: Optional[bytes] = None  # Not used - envelope contains kwargs
    context: Optional[bytes] = None  # Serialized contextvars.Context
    schedule: Optional[dict[str, Any]] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    available_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_run_time: Optional[datetime] = None
    result_id: Optional[str] = None

    # Retry and locking fields
    retries: int = 0
    max_retries: int = 3
    retry_backoff: int = 1
    lock_id: Optional[str] = None
    locked_until: Optional[datetime] = None


@dataclass
class ReservedTask:
    """A task that has been reserved for execution by a worker.

    This represents a task that has been claimed by a worker but
    not yet completed. It contains the minimal information needed
    for task execution.

    Attributes:
        task_id: Unique identifier of the reserved task.
        func: Serialized callable envelope containing function to execute.
        context: Serialized contextvars.Context for task execution.
        started_at: UTC timestamp when task was reserved by worker.

    Example:
        >>> reserved = ReservedTask(
        ...     task_id="abc123",
        ...     func=serialized_function,
        ...     started_at=datetime.now(timezone.utc)
        ... )
    """

    task_id: str
    func: bytes  # Serialized callable envelope
    context: Optional[bytes]  # Serialized contextvars.Context
    started_at: datetime


def _now() -> datetime:
    """Return the current UTC time (helper for consistency)."""
    return datetime.now(timezone.utc)
