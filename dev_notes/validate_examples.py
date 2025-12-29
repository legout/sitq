#!/usr/bin/env python3
"""
Validation script for sitq examples.

This script validates that the runnable examples work correctly
and can be executed successfully by users.
"""

import sys
import os
import subprocess
import asyncio

# Add src to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def validate_example(example_path: str, description: str) -> bool:
    """Validate a single example script."""
    print(f"\n🔍 Validating {description}...")

    try:
        # Run the example with timeout
        result = subprocess.run(
            [sys.executable, example_path], timeout=30, capture_output=True, text=True
        )

        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            print(
                f"   Output: {result.stdout.strip() if result.stdout else 'No output'}"
            )
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"   Return code: {result.returncode}")
            if result.stderr:
                print(f"   Error: {result.stderr.strip()}")
            if result.stdout:
                print(f"   Output: {result.stdout.strip()}")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT (30s)")
        return False
    except Exception as e:
        print(f"💥 {description} - ERROR: {e}")
        return False


def main():
    """Validate all runnable examples."""
    print("🚀 sitq Examples Validation")
    print("=" * 50)

    examples_dir = os.path.join(os.path.dirname(__file__), "..", "examples", "basic")

    examples = [
        ("01_end_to_end.py", "End-to-end workflow"),
        ("02_eta_delayed_execution.py", "Delayed execution with ETA"),
        ("03_bounded_concurrency.py", "Bounded concurrency control"),
        ("04_failures_and_tracebacks.py", "Failure handling and tracebacks"),
        ("05_sync_client_with_worker.py", "Sync client with async worker"),
    ]

    all_passed = True

    for example_file, description in examples:
        example_path = os.path.join(examples_dir, example_file)
        passed = validate_example(example_path, description)

        if not passed:
            all_passed = False

    print("\n" + "=" * 50)

    if all_passed:
        print("🎉 ALL EXAMPLES PASSED!")
        print("\n✅ sitq examples are working correctly")
        print("✅ Users can run examples from examples/basic/ directory")
        print("✅ API structure and imports are functional")
        print("✅ All examples complete within 30 seconds")
        return 0
    else:
        print("❌ SOME EXAMPLES FAILED!")
        print("\n⚠️  Please check the failed examples above")
        print("⚠️  Make sure sitq is properly installed")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error during validation: {e}")
        sys.exit(1)
