from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional


@dataclass
class Task:
    """A unit of work that the queue will execute."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    func: bytes = b""  # Serialized callable
    args: Optional[bytes] = None  # Serialized positional arguments
    kwargs: Optional[bytes] = None  # Serialized keyword arguments
    schedule: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    next_run_time: Optional[datetime] = None
    last_run_time: Optional[datetime] = None
    result_id: Optional[str] = None

    # ----- retry & locking -------------------------------------------------
    retries: int = 0
    max_retries: int = 3
    retry_backoff: int = 1  # base back‑off seconds (used by RetryPolicy)
    lock_id: Optional[str] = None
    locked_until: Optional[datetime] = None


@dataclass
class Result:
    """Result of a finished task."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    status: str = "pending"  # "pending", "success", "failed"
    value: Optional[bytes] = None
    traceback: Optional[str] = None
    retry_count: int = 0
    last_retry_at: Optional[datetime] = None
