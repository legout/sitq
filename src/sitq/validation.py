"""Input validation utilities and decorators for sitq.

This module provides reusable validation functions and decorators to ensure
consistent input validation across all sitq components.
"""

from __future__ import annotations

__all__ = ["validate", "ValidationBuilder", "validate_parameters", "retry_async"]

import functools
from datetime import datetime, timezone
from typing import Any, Callable, Optional, TypeVar, Union, get_type_hints

from .exceptions import ValidationError


F = TypeVar("F", bound=Callable[..., Any])


def validate_parameters(**validators) -> Callable[[F], F]:
    """Decorator to validate function parameters.

    Args:
        **validators: Mapping of parameter names to validator functions.

    Returns:
        Decorated function with parameter validation.

    Example:
        @validate_parameters(
            func=validate_callable,
            timeout=validate_positive_number,
            task_id=validate_non_empty_string
        )
        def my_function(func, timeout=30, task_id=None):
            pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature to map positional args to parameter names
            from inspect import signature

            sig = signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate each parameter
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if value is not None:  # Skip None for optional parameters
                        validator(value, param_name)

            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


def validate_callable(value: Any, param_name: str = "parameter") -> None:
    """Validate that value is callable."""
    if not callable(value):
        raise ValidationError(
            f"{param_name} must be callable", parameter=param_name, value=value
        )


def validate_non_empty_string(value: Any, param_name: str = "parameter") -> None:
    """Validate that value is a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(
            f"{param_name} must be a non-empty string",
            parameter=param_name,
            value=value,
        )


def validate_positive_number(value: Any, param_name: str = "parameter") -> None:
    """Validate that value is a positive number."""
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValidationError(
            f"{param_name} must be a positive number", parameter=param_name, value=value
        )


def validate_non_negative_number(value: Any, param_name: str = "parameter") -> None:
    """Validate that value is a non-negative number."""
    if not isinstance(value, (int, float)) or value < 0:
        raise ValidationError(
            f"{param_name} must be a non-negative number",
            parameter=param_name,
            value=value,
        )


def validate_integer(value: Any, param_name: str = "parameter") -> None:
    """Validate that value is an integer."""
    if not isinstance(value, int):
        raise ValidationError(
            f"{param_name} must be an integer", parameter=param_name, value=value
        )


def validate_string(value: Any, param_name: str = "parameter") -> None:
    """Validate that value is a string."""
    if not isinstance(value, str):
        raise ValidationError(
            f"{param_name} must be a string", parameter=param_name, value=value
        )


def validate_list(value: Any, param_name: str = "parameter") -> None:
    """Validate that value is a list."""
    if not isinstance(value, list):
        raise ValidationError(
            f"{param_name} must be a list", parameter=param_name, value=value
        )


def validate_dict(value: Any, param_name: str = "parameter") -> None:
    """Validate that value is a dictionary."""
    if not isinstance(value, dict):
        raise ValidationError(
            f"{param_name} must be a dictionary", parameter=param_name, value=value
        )


def validate_timezone_aware_datetime(value: Any, param_name: str = "parameter") -> None:
    """Validate that value is a timezone-aware datetime."""
    if not isinstance(value, datetime):
        raise ValidationError(
            f"{param_name} must be a datetime", parameter=param_name, value=value
        )

    if value.tzinfo is None:
        raise ValidationError(
            f"{param_name} must be timezone-aware", parameter=param_name, value=value
        )


def validate_optional(
    validator: Callable[[Any, str], None], allow_none: bool = True
) -> Callable[[Any, str], None]:
    """Create a validator for optional parameters.

    Args:
        validator: Base validator to apply when value is not None.
        allow_none: Whether None values are allowed.

    Returns:
        Validator function that handles Optional values.
    """

    def optional_validator(value: Any, param_name: str = "parameter") -> None:
        if value is None:
            if not allow_none:
                raise ValidationError(
                    f"{param_name} cannot be None", parameter=param_name, value=value
                )
            return

        validator(value, param_name)

    return optional_validator


def validate_range(
    min_val: Optional[Union[int, float]] = None,
    max_val: Optional[Union[int, float]] = None,
) -> Callable[[Any, str], None]:
    """Create a range validator for numeric values.

    Args:
        min_val: Minimum allowed value (inclusive).
        max_val: Maximum allowed value (inclusive).

    Returns:
        Validator function for range checking.
    """

    def range_validator(value: Any, param_name: str = "parameter") -> None:
        if not isinstance(value, (int, float)):
            raise ValidationError(
                f"{param_name} must be a number for range validation",
                parameter=param_name,
                value=value,
            )

        if min_val is not None and value < min_val:
            raise ValidationError(
                f"{param_name} must be at least {min_val}",
                parameter=param_name,
                value=value,
            )

        if max_val is not None and value > max_val:
            raise ValidationError(
                f"{param_name} must be at most {max_val}",
                parameter=param_name,
                value=value,
            )

    return range_validator


def validate_choices(choices: list[Any]) -> Callable[[Any, str], None]:
    """Create a validator for allowed choices.

    Args:
        choices: List of allowed values.

    Returns:
        Validator function for choice checking.
    """

    def choice_validator(value: Any, param_name: str = "parameter") -> None:
        if value not in choices:
            raise ValidationError(
                f"{param_name} must be one of {choices}",
                parameter=param_name,
                value=value,
            )

    return choice_validator


def validate_string_length(
    min_length: Optional[int] = None, max_length: Optional[int] = None
) -> Callable[[Any, str], None]:
    """Create a validator for string length.

    Args:
        min_length: Minimum allowed length.
        max_length: Maximum allowed length.

    Returns:
        Validator function for string length checking.
    """

    def length_validator(value: Any, param_name: str = "parameter") -> None:
        if not isinstance(value, str):
            raise ValidationError(
                f"{param_name} must be a string for length validation",
                parameter=param_name,
                value=value,
            )

        length = len(value)

        if min_length is not None and length < min_length:
            raise ValidationError(
                f"{param_name} must be at least {min_length} characters long",
                parameter=param_name,
                value=value,
            )

        if max_length is not None and length > max_length:
            raise ValidationError(
                f"{param_name} must be at most {max_length} characters long",
                parameter=param_name,
                value=value,
            )

    return length_validator


class ValidationBuilder:
    """Builder for complex validation rules."""

    def __init__(self, value: Any, param_name: str = "parameter"):
        self.value = value
        self.param_name = param_name
        self.errors = []

    def is_required(self) -> ValidationBuilder:
        """Mark parameter as required (not None)."""
        if self.value is None:
            self.errors.append(f"{self.param_name} is required")
        return self

    def is_callable(self) -> ValidationBuilder:
        """Check if value is callable."""
        if self.value is not None and not callable(self.value):
            self.errors.append(f"{self.param_name} must be callable")
        return self

    def is_string(self) -> ValidationBuilder:
        """Check if value is a string."""
        if self.value is not None and not isinstance(self.value, str):
            self.errors.append(f"{self.param_name} must be a string")
        return self

    def is_positive_number(self) -> ValidationBuilder:
        """Check if value is a positive number."""
        if self.value is not None:
            if not isinstance(self.value, (int, float)) or self.value <= 0:
                self.errors.append(f"{self.param_name} must be a positive number")
        return self

    def is_non_negative(self) -> ValidationBuilder:
        """Check if value is a non-negative number."""
        if self.value is not None:
            if not isinstance(self.value, (int, float)) or self.value < 0:
                self.errors.append(f"{self.param_name} must be non-negative")
        return self

    def is_timezone_aware(self) -> ValidationBuilder:
        """Check if value is a timezone-aware datetime."""
        if self.value is not None:
            if not isinstance(self.value, datetime):
                self.errors.append(f"{self.param_name} must be a datetime")
            elif self.value.tzinfo is None:
                self.errors.append(f"{self.param_name} must be timezone-aware")
        return self

    def min_length(self, min_len: int) -> ValidationBuilder:
        """Check minimum string length."""
        if self.value is not None and isinstance(self.value, str):
            if len(self.value) < min_len:
                self.errors.append(
                    f"{self.param_name} must be at least {min_len} characters"
                )
        return self

    def max_length(self, max_len: int) -> ValidationBuilder:
        """Check maximum string length."""
        if self.value is not None and isinstance(self.value, str):
            if len(self.value) > max_len:
                self.errors.append(
                    f"{self.param_name} must be at most {max_len} characters"
                )
        return self

    def in_range(
        self, min_val: Union[int, float], max_val: Union[int, float]
    ) -> ValidationBuilder:
        """Check if value is in numeric range."""
        if self.value is not None:
            if not isinstance(self.value, (int, float)):
                self.errors.append(
                    f"{self.param_name} must be a number for range validation"
                )
            elif not (min_val <= self.value <= max_val):
                self.errors.append(
                    f"{self.param_name} must be between {min_val} and {max_val}"
                )
        return self

    def in_choices(self, choices: list[Any]) -> ValidationBuilder:
        """Check if value is in allowed choices."""
        if self.value is not None and self.value not in choices:
            self.errors.append(f"{self.param_name} must be one of {choices}")
        return self

    def validate(self) -> None:
        """Perform validation and raise ValidationError if any errors found."""
        if self.errors:
            raise ValidationError(
                "; ".join(self.errors), parameter=self.param_name, value=self.value
            )


def validate(value: Any, param_name: str = "parameter") -> ValidationBuilder:
    """Create a new ValidationBuilder instance.

    Args:
        value: The value to validate
        param_name: Name of the parameter being validated

    Returns:
        ValidationBuilder instance for fluent validation
    """
    return ValidationBuilder(value, param_name)


import asyncio
import random
import functools
from typing import Callable, Type, Union, List, Any


def retry_async(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: List[Type[Exception]] | None = None,
) -> Callable:
    """Decorator for async functions to add retry logic with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts (including initial attempt)
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Multiplier for exponential backoff
        jitter: Whether to add random jitter to prevent thundering herd
        retryable_exceptions: List of exception types that should trigger retries

    Returns:
        Decorated function that will retry on transient failures
    """
    if retryable_exceptions is None:
        # Default retryable exceptions - typically network/database issues
        retryable_exceptions = [
            ConnectionError,
            TimeoutError,
            # Add other transient exceptions as needed
        ]

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if this exception type is retryable
                    if not retryable_exceptions or not any(
                        isinstance(e, exc_type) for exc_type in retryable_exceptions
                    ):
                        # Not a retryable exception, re-raise immediately
                        raise e

                    # If this is the last attempt, re-raise the exception
                    if attempt == max_attempts - 1:
                        raise e

                    # Calculate delay for next attempt
                    delay = min(base_delay * (backoff_factor**attempt), max_delay)

                    if jitter:
                        # Add random jitter (±25% of delay)
                        jitter_amount = delay * 0.25
                        delay += random.uniform(-jitter_amount, jitter_amount)

                    # Ensure delay is non-negative
                    delay = max(0, delay)

                    # Log retry attempt (would use proper logging in real implementation)
                    print(
                        f"Retry {attempt + 1}/{max_attempts} after {delay:.2f}s for {func.__name__}: {e}"
                    )

                    # Wait before next attempt
                    await asyncio.sleep(delay)

            # This should never be reached, but just in case
            raise last_exception

        return wrapper

    return decorator


def retry_sync(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: List[Type[Exception]] | None = None,
) -> Callable:
    """Decorator for sync functions to add retry logic with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts (including initial attempt)
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Multiplier for exponential backoff
        jitter: Whether to add random jitter to prevent thundering herd
        retryable_exceptions: List of exception types that should trigger retries

    Returns:
        Decorated function that will retry on transient failures
    """
    if retryable_exceptions is None:
        retryable_exceptions = [
            ConnectionError,
            TimeoutError,
        ]

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            import random

            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if this exception type is retryable
                    if not retryable_exceptions or not any(
                        isinstance(e, exc_type) for exc_type in retryable_exceptions
                    ):
                        # Not a retryable exception, re-raise immediately
                        raise e

                    # If this is the last attempt, re-raise the exception
                    if attempt == max_attempts - 1:
                        raise e

                    # Calculate delay for next attempt
                    delay = min(base_delay * (backoff_factor**attempt), max_delay)

                    if jitter:
                        # Add random jitter (±25% of delay)
                        jitter_amount = delay * 0.25
                        delay += random.uniform(-jitter_amount, jitter_amount)

                    # Ensure delay is non-negative
                    delay = max(0, delay)

                    # Log retry attempt
                    print(
                        f"Retry {attempt + 1}/{max_attempts} after {delay:.2f}s for {func.__name__}: {e}"
                    )

                    # Wait before next attempt
                    time.sleep(delay)

            # This should never be reached, but just in case
            raise last_exception

        return wrapper

    return decorator
