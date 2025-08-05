"""
Simple serializer abstractions.
"""

from __future__ import annotations

import json
import cloudpickle
from typing import Any


class Serializer:
    """Base serializer interface."""

    def dumps(self, obj: Any) -> bytes:
        raise NotImplementedError

    def loads(self, data: bytes) -> Any:
        raise NotImplementedError


class PickleSerializer(Serializer):
    """Uses cloudpickle – can handle closures, lambdas, etc."""

    def dumps(self, obj: Any) -> bytes:
        return cloudpickle.dumps(obj)

    def loads(self, data: bytes) -> Any:
        return cloudpickle.loads(data)


class JsonSerializer(Serializer):
    """JSON‑compatible serializer – works only for importable callables."""

    def dumps(self, obj: Any) -> bytes:
        return json.dumps(obj).encode("utf-8")

    def loads(self, data: bytes) -> Any:
        return json.loads(data.decode("utf-8"))
