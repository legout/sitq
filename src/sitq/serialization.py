"""Internal serialization abstraction for sitq.

This module provides the serialization protocol and default implementation
used internally by sitq for task payloads and results. The serialization
API is not exposed as a public pluggable interface in v1.
"""

from __future__ import annotations

import cloudpickle
from typing import Protocol, runtime_checkable


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
    handle.
    """

    def dumps(self, obj: object) -> bytes:
        """Serialize a Python object to bytes using cloudpickle.

        Args:
            obj: The Python object to serialize.

        Returns:
            Serialized bytes representation of the object.
        """
        return cloudpickle.dumps(obj)

    def loads(self, data: bytes) -> object:
        """Deserialize bytes back to a Python object using cloudpickle.

        Args:
            data: The bytes to deserialize.

        Returns:
            The original Python object.
        """
        return cloudpickle.loads(data)
