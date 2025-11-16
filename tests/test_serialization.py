"""
Unit tests for serializer behavior and payload round-tripping.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sitq.serialization import CloudpickleSerializer


def test_cloudpickle_serializer_basic_types():
    """Test serialization of basic Python types."""
    serializer = CloudpickleSerializer()

    # Test basic types
    test_cases = [
        "hello world",
        42,
        3.14,
        True,
        None,
        [1, 2, 3],
        {"key": "value"},
        (1, 2, 3),
    ]

    for obj in test_cases:
        serialized = serializer.dumps(obj)
        deserialized = serializer.loads(serialized)
        assert deserialized == obj


def test_cloudpickle_serializer_callable():
    """Test serialization of callable objects."""
    serializer = CloudpickleSerializer()

    def test_function(x, y):
        return x + y

    # Serialize and deserialize the function
    serialized = serializer.dumps(test_function)
    deserialized = serializer.loads(serialized)

    # Test that the function works the same
    assert deserialized(5, 3) == 8


def test_cloudpickle_serializer_lambda():
    """Test serialization of lambda functions."""
    serializer = CloudpickleSerializer()

    # Test lambda (convert to def for linting)
    def lambda_func(x):
        return x * 2

    serialized = serializer.dumps(lambda_func)
    deserialized = serializer.loads(serialized)

    assert deserialized(5) == 10


def test_cloudpickle_serializer_closure():
    """Test serialization of functions with closures."""
    serializer = CloudpickleSerializer()

    def create_multiplier(factor):
        def multiply(x):
            return x * factor

        return multiply

    # Create a function with closure
    multiply_by_3 = create_multiplier(3)

    # Serialize and deserialize
    serialized = serializer.dumps(multiply_by_3)
    deserialized = serializer.loads(serialized)

    # Test that the closure still works
    assert deserialized(5) == 15


def test_cloudpickle_serializer_complex_object():
    """Test serialization of complex Python objects."""
    serializer = CloudpickleSerializer()

    class TestClass:
        def __init__(self, name, values):
            self.name = name
            self.values = values

        def __eq__(self, other):
            return (
                isinstance(other, TestClass)
                and self.name == other.name
                and self.values == other.values
            )

    # Test complex object
    obj = TestClass("test", [1, 2, 3])
    serialized = serializer.dumps(obj)
    deserialized = serializer.loads(serialized)

    assert deserialized == obj


def test_task_queue_uses_default_serializer():
    """Test that TaskQueue uses CloudpickleSerializer by default."""
    from src.sitq.queue import TaskQueue

    # Mock backend
    class MockBackend:
        pass

    task_queue = TaskQueue(MockBackend())
    assert isinstance(task_queue.serializer, CloudpickleSerializer)


def test_task_queue_accepts_custom_serializer():
    """Test that TaskQueue accepts custom serializer."""
    from src.sitq.queue import TaskQueue

    # Mock backend
    class MockBackend:
        pass

    # Custom serializer
    class CustomSerializer:
        def dumps(self, obj):
            return b"custom"

        def loads(self, data):
            return "custom_result"

    custom = CustomSerializer()
    task_queue = TaskQueue(MockBackend(), serializer=custom)
    assert task_queue.serializer is custom


def test_worker_uses_default_serializer():
    """Test that Worker uses CloudpickleSerializer by default."""
    from src.sitq.worker import Worker

    # Mock backend
    class MockBackend:
        pass

    worker = Worker(MockBackend())
    assert isinstance(worker.serializer, CloudpickleSerializer)


def test_worker_accepts_custom_serializer():
    """Test that Worker accepts custom serializer."""
    from src.sitq.worker import Worker

    # Mock backend
    class MockBackend:
        pass

    # Custom serializer
    class CustomSerializer:
        def dumps(self, obj):
            return b"custom"

        def loads(self, data):
            return "custom_result"

    custom = CustomSerializer()
    worker = Worker(MockBackend(), serializer=custom)
    assert worker.serializer is custom


def test_serializer_protocol():
    """Test that serializers conform to the protocol."""
    from src.sitq.serialization import Serializer
    import inspect

    # Check protocol methods
    methods = [
        name
        for name, method in inspect.getmembers(Serializer, predicate=inspect.isfunction)
    ]
    assert "dumps" in methods
    assert "loads" in methods

    # Check CloudpickleSerializer has required methods
    serializer = CloudpickleSerializer()
    assert hasattr(serializer, "dumps")
    assert hasattr(serializer, "loads")
    assert callable(serializer.dumps)
    assert callable(serializer.loads)
