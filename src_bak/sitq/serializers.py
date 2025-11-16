"""
Serializer abstractions with support for a canonical task envelope.

We support two serializer strategies:
- PickleSerializer: uses cloudpickle and can serialize callables and complex
  Python objects (binary).
- JsonSerializer: uses JSON and supports import-path strings for callables.
  It will convert callable objects to import paths when serializing envelopes.
"""

from __future__ import annotations

import json
import importlib
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
    """
    JSON‑compatible serializer – intended for simple, importable callables and
    JSON-serializable arguments. When serializing a canonical envelope (a dict
    with keys 'func', 'args', 'kwargs'), if the 'func' value is a callable we
    convert it to its import path string (e.g. 'mypkg.module.func').
    """

    @staticmethod
    def _callable_to_import_path(obj: Any) -> str:
        return f"{obj.__module__}.{obj.__qualname__}"

    @staticmethod
    def _try_resolve_import_path(path: str):
        """
        Resolve 'module.attr' to a Python object. On failure return the original
        string (best-effort behaviour).
        """
        try:
            module_name, _, attr = path.rpartition(".")
            module = importlib.import_module(module_name)
            return getattr(module, attr)
        except Exception:
            return path

    def dumps(self, obj: Any) -> bytes:
        # If top-level callable -> encode its import path
        if callable(obj):
            return json.dumps(self._callable_to_import_path(obj)).encode("utf-8")

        # If canonical envelope and contains a callable under 'func', replace it
        if isinstance(obj, dict) and "func" in obj and callable(obj["func"]):
            obj = dict(obj)
            obj["func"] = self._callable_to_import_path(obj["func"])

        # Convert tuples -> lists so JSON is stable for positional args
        def _default(o):
            if isinstance(o, tuple):
                return list(o)
            raise TypeError(f"Object of type {type(o)} is not JSON serializable")

        return json.dumps(obj, default=_default).encode("utf-8")

    def loads(self, data: bytes) -> Any:
        obj = json.loads(data.decode("utf-8"))

        # If a single import-path string was serialized for a callable, resolve it
        if isinstance(obj, str) and "." in obj:
            resolved = self._try_resolve_import_path(obj)
            return resolved

        # If canonical envelope with func as import path string, resolve it
        if isinstance(obj, dict) and "func" in obj and isinstance(obj["func"], str):
            obj = dict(obj)
            obj["func"] = self._try_resolve_import_path(obj["func"])

        return obj
