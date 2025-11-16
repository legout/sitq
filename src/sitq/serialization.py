"""
Internal serializer abstraction and default cloudpickle implementation.

This module provides a simple Serializer protocol and CloudpickleSerializer
implementation for encoding task payloads and results.
"""

import cloudpickle
from typing import Protocol, Any


class Serializer(Protocol):
    """
    Protocol for serializers that can encode and decode Python objects.

    This protocol is used internally by TaskQueue, Worker, and backends
    to serialize task payloads and results.
    """

    def dumps(self, obj: Any) -> bytes:
        """
        Serialize a Python object to bytes.

        Args:
            obj: The object to serialize

        Returns:
            bytes: Serialized representation of the object
        """
        ...

    def loads(self, data: bytes) -> Any:
        """
        Deserialize bytes back to a Python object.

        Args:
            data: The bytes to deserialize

        Returns:
            object: The deserialized Python object
        """
        ...


class CloudpickleSerializer:
    """
    Default cloudpickle-based serializer implementation.

    Uses cloudpickle.dumps and cloudpickle.loads to handle arbitrary
    Python objects including callables, closures, and complex data structures.
    """

    def dumps(self, obj: Any) -> bytes:
        """Serialize object to bytes using cloudpickle."""
        return cloudpickle.dumps(obj)

    def loads(self, data: bytes) -> Any:
        """Deserialize bytes to object using cloudpickle."""
        return cloudpickle.loads(data)
