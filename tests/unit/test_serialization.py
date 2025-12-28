"""Tests for serialization module."""

import pytest
from src.sitq.serialization import Serializer, CloudpickleSerializer


def test_cloudpickle_serializer_protocol():
    """Test that CloudpickleSerializer implements the Serializer protocol."""
    serializer = CloudpickleSerializer()
    assert isinstance(serializer, Serializer)


def test_cloudpickle_serializer_round_trip():
    """Test that CloudpickleSerializer can serialize and deserialize objects."""
    serializer = CloudpickleSerializer()

    # Test simple objects
    test_cases = [
        42,
        "hello world",
        [1, 2, 3],
        {"key": "value"},
        (1, 2, 3),
        None,
        True,
        False,
    ]

    for obj in test_cases:
        serialized = serializer.dumps(obj)
        deserialized = serializer.loads(serialized)
        assert deserialized == obj


def test_cloudpickle_serializer_functions():
    """Test that CloudpickleSerializer can handle functions."""
    serializer = CloudpickleSerializer()

    def test_func(x, y):
        return x + y

    # Serialize the function
    serialized_func = serializer.dumps(test_func)

    # Deserialize and call the function
    deserialized_func = serializer.loads(serialized_func)
    result = deserialized_func(3, 4)
    assert result == 7


def test_cloudpickle_serializer_complex_objects():
    """Test that CloudpickleSerializer can handle complex objects."""
    serializer = CloudpickleSerializer()

    # Test with lambda
    lambda_func = lambda x: x * 2
    serialized = serializer.dumps(lambda_func)
    deserialized = serializer.loads(serialized)
    assert deserialized(5) == 10

    # Test with class
    class TestClass:
        def __init__(self, value):
            self.value = value

        def get_value(self):
            return self.value

    obj = TestClass(42)
    serialized = serializer.dumps(obj)
    deserialized = serializer.loads(serialized)
    assert deserialized.get_value() == 42


def test_cloudpickle_serializer_task_payload():
    """Test serialization of task payload envelope as specified in requirements."""
    serializer = CloudpickleSerializer()

    def example_task_func(name, count=1):
        return f"Hello {name}! Count: {count}"

    # Create task payload envelope as specified in the requirements
    envelope = {"func": example_task_func, "args": ("Alice",), "kwargs": {"count": 3}}

    # Serialize the envelope
    serialized = serializer.dumps(envelope)
    assert isinstance(serialized, bytes)

    # Deserialize the envelope
    deserialized = serializer.loads(serialized)
    assert isinstance(deserialized, dict)
    assert "func" in deserialized
    assert "args" in deserialized
    assert "kwargs" in deserialized

    # Test that the deserialized function works
    func = deserialized["func"]
    args = deserialized["args"]
    kwargs = deserialized["kwargs"]
    result = func(*args, **kwargs)
    assert result == "Hello Alice! Count: 3"


def test_cloudpickle_serializer_bytes_type():
    """Test that serializer returns bytes and accepts bytes."""
    serializer = CloudpickleSerializer()

    obj = {"test": "data"}
    serialized = serializer.dumps(obj)

    # Ensure it returns bytes
    assert isinstance(serialized, bytes)

    # Ensure loads can handle the bytes
    deserialized = serializer.loads(serialized)
    assert deserialized == obj
