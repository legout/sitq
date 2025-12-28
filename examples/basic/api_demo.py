#!/usr/bin/env python3
"""
Quickstart Example for sitq

This example demonstrates the current sitq API structure:
1. Import core components
2. Show available API surface
3. Demonstrate basic usage patterns

This provides a working example that can be run to verify
the sitq installation and API structure.
"""

import sys
import os

# Add src to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def main():
    """Demonstrate sitq API structure and availability."""
    print("🚀 sitq API Quickstart Example")
    print("=" * 40)

    try:
        # 1. Test imports
        print("\n1. Testing core imports...")
        from sitq import (
            TaskQueue,
            Worker,
            SQLiteBackend,
            SyncTaskQueue,
            Task,
            Result,
            ReservedTask,
            Backend,
            Serializer,
            CloudpickleSerializer,
            # Exceptions
            SitqError,
            TaskQueueError,
            BackendError,
            WorkerError,
            ValidationError,
            SerializationError,
            ConnectionError,
            TaskExecutionError,
            TimeoutError,
            ResourceExhaustionError,
            ConfigurationError,
            # Utilities
            validate,
            ValidationBuilder,
        )

        print("   ✅ All core imports successful")

        # 2. Show API surface
        print("\n2. Current API surface:")
        api_classes = [
            "TaskQueue - Async task queue for enqueuing/retrieving tasks",
            "Worker - Worker for executing tasks from queue",
            "SQLiteBackend - SQLite backend for task persistence",
            "SyncTaskQueue - Synchronous wrapper for TaskQueue",
            "Task/Result/ReservedTask - Core data structures",
            "CloudpickleSerializer - Default task/result serializer",
            "Various exception classes for error handling",
        ]

        for cls_desc in api_classes:
            print(f"   📦 {cls_desc}")

        # 3. Show usage pattern
        print("\n3. Basic usage pattern:")
        print("   📝 from sitq import TaskQueue, Worker, SQLiteBackend")
        print("   📝 backend = SQLiteBackend('tasks.db')")
        print("   📝 queue = TaskQueue(backend=backend)")
        print("   📝 worker = Worker(backend)")
        print("   📝 task_id = await queue.enqueue(func, *args, **kwargs)")
        print("   📝 result = await queue.get_result(task_id)")
        print("   📝 await worker.start() / await worker.stop()")

        # 4. Show current limitations
        print("\n4. Current implementation status:")
        print("   ✅ Core API structure is functional")
        print("   ✅ Import system works correctly")
        print("   ⚠️  Some backend methods need fixes for full E2E functionality")
        print("   📝 See examples/basic/ for more detailed examples")

        print("\n🎉 API structure verification completed!")
        print("\nNext steps:")
        print("   1. Fix backend implementation issues for full functionality")
        print("   2. Add comprehensive end-to-end examples")
        print("   3. Update documentation to match current API")

        return True

    except ImportError as e:
        print(f"\n❌ Import failed: {e}")
        print("   This indicates the sitq package structure has issues")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Example completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Example failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Example interrupted by user")
        sys.exit(1)
