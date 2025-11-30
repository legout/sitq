"""Core data models for sitq."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any


@dataclass
class Result:
    """Result of a finished task execution."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    status: str = "pending"  # "success", "failed"
    value: Optional[bytes] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    enqueued_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


@dataclass
class Task:
    """A unit of work that the queue will execute."""

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
    """A task that has been reserved for execution by a worker."""

    task_id: str
    func: bytes  # Serialized callable envelope
    context: Optional[bytes]  # Serialized contextvars.Context
    started_at: datetime


def _now() -> datetime:
    """Return the current UTC time (helper for consistency)."""
    return datetime.now(timezone.utc)
