"""Internal serialization abstraction for sitq.

This module provides the serialization protocol and default implementation
used internally by sitq for task payloads and results. The serialization
API is not exposed as a public pluggable interface in v1.
"""

from __future__ import annotations

__all__ = ["Serializer", "CloudpickleSerializer", "TaskEnvelope"]

import cloudpickle
from typing import Protocol, runtime_checkable, TypedDict, Dict, Any, Optional, cast

from .exceptions import SerializationError, ValidationError
from .validation import validate


class TaskEnvelope(TypedDict):
    """Standard task envelope format for sitq.

    This envelope format ensures consistent serialization across all
    sitq components (TaskQueue, Worker, SyncTaskQueue).
    """

    func: Any  # The callable to execute
    args: tuple  # Positional arguments for the function
    kwargs: Dict[str, Any]  # Keyword arguments for the function


@runtime_checkable
class Serializer(Protocol):
    """Protocol for serializing and deserializing Python objects.

    This protocol defines the interface used internally by sitq components
    to encode task payloads and results for storage in backends.
    """

    def dumps(self, obj: object) -> bytes:
        """Serialize a Python object to bytes.

        Args:
            obj: The Python object to serialize.

        Returns:
            Serialized bytes representation of the object.
        """
        ...

    def loads(self, data: bytes) -> object:
        """Deserialize bytes back to a Python object.

        Args:
            data: The bytes to deserialize.

        Returns:
            The original Python object.
        """
        ...


class CloudpickleSerializer:
    """Default serializer implementation using cloudpickle.

    This serializer uses cloudpickle to handle Python objects that may include
    functions, classes, and other complex types that standard pickle cannot
    handle. It provides the primary serialization mechanism for sitq tasks
    and results.

    Attributes:
        No additional attributes beyond the Serializer protocol.

    Example:
        >>> serializer = CloudpickleSerializer()
        >>> data = serializer.dumps(my_function)
        >>> func = serializer.loads(data)
    """

    def dumps(self, obj: object) -> bytes:
        """Serialize a Python object to bytes using cloudpickle.

        Args:
            obj: The Python object to serialize.

        Returns:
            Serialized bytes representation of the object.
        """
        try:
            return cloudpickle.dumps(obj)
        except Exception as e:
            raise SerializationError(
                f"Failed to serialize object: {e} - ensure object is serializable and compatible with cloudpickle",
                cause=e,
            ) from e

    def loads(self, data: bytes) -> object:
        """Deserialize bytes back to a Python object using cloudpickle.

        Args:
            data: The bytes to deserialize.

        Returns:
            The original Python object.
        """
        # Validate input
        validate(data, "data").is_required().validate()

        try:
            return cloudpickle.loads(data)
        except Exception as e:
            raise SerializationError(
                f"Failed to deserialize data: {e} - ensure data was serialized with the same format",
                cause=e,
            ) from e

    def serialize_task_envelope(
        self, func: Any, args: tuple = (), kwargs: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Serialize a task using the standard envelope format.

        Args:
            func: The callable to execute.
            args: Positional arguments for the function.
            kwargs: Keyword arguments for the function.

        Returns:
            Serialized task envelope bytes.
        """
        envelope: TaskEnvelope = {"func": func, "args": args, "kwargs": kwargs or {}}
        return self.dumps(envelope)

    def deserialize_task_envelope(self, data: bytes) -> TaskEnvelope:
        """Deserialize a task envelope and validate the format.

        Args:
            data: The serialized envelope bytes.

        Returns:
            Validated task envelope dictionary.

        Raises:
            ValueError: If the envelope format is invalid.
        """
        envelope = self.loads(data)

        # Validate envelope structure
        if not isinstance(envelope, dict):
            raise ValueError(
                "Task envelope must be a dictionary - ensure envelope is properly structured"
            )

        required_keys = {"func", "args", "kwargs"}
        missing_keys = required_keys - set(envelope.keys())
        if missing_keys:
            raise ValueError(
                f"Task envelope missing required keys: {missing_keys} - ensure envelope contains 'func', 'args', and 'kwargs'"
            )

        if not isinstance(envelope["args"], tuple):
            raise ValueError(
                "Task envelope 'args' must be a tuple - ensure function arguments are properly formatted"
            )

        if not isinstance(envelope["kwargs"], dict):
            raise ValueError(
                "Task envelope 'kwargs' must be a dictionary - ensure keyword arguments are properly formatted"
            )

        return cast(TaskEnvelope, envelope)

    def serialize_result(self, result: Any) -> bytes:
        """Serialize a task result.

        Args:
            result: The result value to serialize.

        Returns:
            Serialized result bytes.
        """
        return self.dumps(result)

    def deserialize_result(self, data: bytes) -> Any:
        """Deserialize a task result.

        Args:
            data: The serialized result bytes.

        Returns:
            The original result value.
        """
        return self.loads(data)
