"""
Result data model for completed task outcomes.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class Result:
    """
    Data model representing the outcome of a task execution.
    
    Contains status, result data, error information, and timing details
    for tasks executed through the TaskQueue.
    """
    
    task_id: str
    status: str  # "success" or "failed"
    value: Optional[Any] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    enqueued_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    
    def is_success(self) -> bool:
        """Check if the task completed successfully."""
        return self.status == "success"
    
    def is_failed(self) -> bool:
        """Check if the task failed."""
        return self.status == "failed"
