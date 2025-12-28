#!/usr/bin/env python3
"""Test script to verify sitq module structure and docstring coverage."""

import sys
import os
import importlib.util


def test_module_import():
    """Test if sitq module can be imported with all expected symbols."""

    print("Testing sitq module import...")

    try:
        # Change to src directory
        sys.path.insert(0, "src")

        # Import the module
        spec = importlib.util.spec_from_file_location("sitq", "src/sitq/__init__.py")
        sitq = importlib.util.module_from_spec(spec)

        # Check if all expected symbols are available
        expected_symbols = [
            "TaskQueue",
            "Worker",
            "SyncTaskQueue",
            "Task",
            "Result",
            "ReservedTask",
            "Backend",
            "SQLiteBackend",
            "Serializer",
            "CloudpickleSerializer",
            "SitqError",
            "TaskQueueError",
            "BackendError",
            "WorkerError",
            "ValidationError",
            "SerializationError",
            "ConnectionError",
            "TaskExecutionError",
            "TimeoutError",
            "ResourceExhaustionError",
            "ConfigurationError",
            "validate",
            "ValidationBuilder",
        ]

        missing_symbols = []
        for symbol in expected_symbols:
            if not hasattr(sitq, symbol):
                missing_symbols.append(symbol)

        if missing_symbols:
            print(f"❌ Missing symbols: {missing_symbols}")
            return False
        else:
            print("✅ All expected symbols are available")
            return True

    except Exception as e:
        print(f"❌ Failed to import sitq: {e}")
        return False


def test_docstring_coverage():
    """Test basic docstring coverage for key classes."""

    print("Testing docstring coverage...")

    try:
        sys.path.insert(0, "src")
        import sitq

        # Test key classes have docstrings
        classes_to_test = [
            ("TaskQueue", sitq.TaskQueue),
            ("Worker", sitq.Worker),
            ("SyncTaskQueue", sitq.SyncTaskQueue),
            ("SQLiteBackend", sitq.SQLiteBackend),
            ("CloudpickleSerializer", sitq.CloudpickleSerializer),
            ("Result", sitq.Result),
            ("Task", sitq.Task),
            ("ReservedTask", sitq.ReservedTask),
        ]

        missing_docs = []
        for name, cls in classes_to_test:
            if not cls.__doc__ or not cls.__doc__.strip():
                missing_docs.append(name)
            else:
                print(f"✅ {name} has docstring")

        if missing_docs:
            print(f"❌ Missing docstrings: {missing_docs}")
            return False
        else:
            print("✅ All key classes have docstrings")
            return True

    except Exception as e:
        print(f"❌ Failed to test docstrings: {e}")
        return False


def main():
    """Run all tests."""

    print("Running sitq module and docstring verification tests...\n")

    import_test = test_module_import()
    docstring_test = test_docstring_coverage()

    if import_test and docstring_test:
        print("\n✅ All tests passed! sitq module is ready for documentation.")
        return True
    else:
        print("\n❌ Some tests failed. Please fix issues before proceeding.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
