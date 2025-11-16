"""
Retry policy handling – calculates back‑off delays for failed tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Type


@dataclass
class RetryPolicy:
    """
    Configurable retry policy.

    Parameters
    ----------
    max_retries : int
        Maximum number of retry attempts.
    initial_delay : int
        Base delay (seconds) for the first retry.
    strategy : str
        Either ``"exponential"`` or ``"linear"``.
    factor : float
        Multiplicative factor for exponential back‑off.
    retry_on : Tuple[Exception, ...]
        Exception types that trigger a retry.
    """

    max_retries: int = 3
    initial_delay: int = 1
    strategy: str = "exponential"
    factor: float = 2.0
    retry_on: Tuple[Type[BaseException], ...] = (Exception,)

    def get_delay(self, retry_count: int) -> int:
        """Return the delay (seconds) for ``retry_count`` (1‑based)."""
        if retry_count <= 0:
            raise ValueError("retry_count must be >= 1")

        if self.strategy == "exponential":
            return int(self.initial_delay * (self.factor ** (retry_count - 1)))
        return self.initial_delay * retry_count
