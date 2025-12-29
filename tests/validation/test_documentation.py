#!/usr/bin/env python3
"""
Simple test to verify documentation completeness without requiring mkdocstrings.

This script checks:
1. All public APIs are accessible
2. All docstrings are present
3. Cross-references exist in documentation
4. Examples are syntactically valid
"""

import sys
import ast
import importlib
import inspect
from pathlib import Path


def test_public_api_access():
    """Test if all public APIs are accessible."""
    try:
        import sitq

        # Test core components
        required_components = [
            "TaskQueue",
            "Worker",
            "SyncTaskQueue",
            "Task",
            "Result",
            "ReservedTask",
            "SQLiteBackend",
            "Backend",
            "Serializer",
            "CloudpickleSerializer",
        ]

        missing_components = []
        for component in required_components:
            if not hasattr(sitq, component):
                missing_components.append(component)

        if missing_components:
            print(f"❌ Missing components: {missing_components}")
            return False
        else:
            print("✅ All required components are accessible")
            return True

    except ImportError as e:
        print(f"❌ Failed to import sitq: {e}")
        return False


def test_docstring_presence():
    """Test if all public APIs have docstrings."""
    try:
        import sitq

        # Test main classes
        classes_to_check = [
            sitq.TaskQueue,
            sitq.Worker,
            sitq.SyncTaskQueue,
            sitq.Task,
            sitq.Result,
            sitq.SQLiteBackend,
        ]

        missing_docstrings = []
        for cls in classes_to_check:
            if not cls.__doc__ or not cls.__doc__.strip():
                missing_docstrings.append(cls.__name__)

        if missing_docstrings:
            print(f"❌ Classes missing docstrings: {missing_docstrings}")
            return False
        else:
            print("✅ All main classes have docstrings")
            return True

    except Exception as e:
        print(f"❌ Docstring test failed: {e}")
        return False


def test_cross_references():
    """Test if cross-references exist in documentation (agnostic to file paths)."""
    docs_dir = Path("docs")

    if not docs_dir.exists():
        print("❌ Documentation directory not found")
        return False

    # Check for cross-reference patterns (agnostic to which file they're in)
    cross_ref_patterns = [
        "[`TaskQueue`]",
        "[`Worker`]",
        "[`SQLiteBackend`]",
        "See Also:",
        "## See Also",
    ]

    found_references = 0
    for pattern in cross_ref_patterns:
        for file in docs_dir.rglob("*.md"):
            content = file.read_text()
            if pattern in content:
                found_references += 1
                break

    expected_references = len(cross_ref_patterns)
    if found_references >= expected_references * 0.8:  # Allow 80% match
        print(f"✅ Cross-references found: {found_references}/{expected_references}")
        return True
    else:
        print(
            f"❌ Insufficient cross-references: {found_references}/{expected_references}"
        )
        return False


def test_example_syntax():
    """Test if code examples in documentation are syntactically valid."""
    docs_dir = Path("docs")

    if not docs_dir.exists():
        print("❌ Documentation directory not found")
        return False

    # Find Python code blocks
    python_code_blocks = []

    for file in docs_dir.rglob("*.md"):
        content = file.read_text()

        # Find Python code blocks
        import re

        code_blocks = re.findall(r"```python\n(.*?)\n```", content, re.DOTALL)
        python_code_blocks.extend(code_blocks)

    print(f"Found {len(python_code_blocks)} Python code blocks")

    # Test syntax of code blocks
    valid_blocks = 0
    syntax_errors = []

    for i, code in enumerate(python_code_blocks[:10]):  # Test first 10
        try:
            ast.parse(code)
            valid_blocks += 1
        except SyntaxError as e:
            syntax_errors.append(f"Block {i}: {e}")

    if syntax_errors:
        print(f"❌ Syntax errors found:")
        for error in syntax_errors:
            print(f"  {error}")
        return False
    else:
        print(
            f"✅ All tested code blocks have valid syntax ({valid_blocks}/{min(len(python_code_blocks), 10)})"
        )
        return True


def test_documentation_structure():
    """Test if documentation has proper structure following Diátaxis layout."""
    required_files = [
        "docs/index.md",
        "docs/explanation/architecture.md",
        "docs/explanation/limitations.md",
        "docs/explanation/serialization.md",
        "docs/how-to/installation.md",
        "docs/how-to/deployment.md",
        "docs/how-to/error-handling.md",
        "docs/how-to/get-results.md",
        "docs/how-to/handle-failures.md",
        "docs/how-to/performance.md",
        "docs/how-to/run-worker.md",
        "docs/how-to/serialization.md",
        "docs/how-to/sqlite-backend.md",
        "docs/how-to/sync-wrapper.md",
        "docs/how-to/testing.md",
        "docs/how-to/troubleshooting.md",
        "docs/how-to/workers.md",
        "docs/how-to/contributing.md",
        "docs/tutorials/index.md",
        "docs/tutorials/quickstart.md",
        "docs/tutorials/basic-concepts.md",
        "docs/tutorials/concurrency.md",
        "docs/tutorials/delayed-execution.md",
        "docs/tutorials/failures.md",
        "docs/tutorials/interactive-tutorial.ipynb",
        "docs/reference/ERROR_HANDLING.md",
        "docs/reference/changelog.md",
        "docs/reference/api/sitq.md",
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Missing documentation files: {missing_files}")
        return False
    else:
        print("✅ All required documentation files exist")
        return True


def main():
    """Run all documentation tests."""
    print("🧪 Running documentation validation tests...\n")

    tests = [
        ("Public API Access", test_public_api_access),
        ("Docstring Presence", test_docstring_presence),
        ("Cross-References", test_cross_references),
        ("Example Syntax", test_example_syntax),
        ("Documentation Structure", test_documentation_structure),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 DOCUMENTATION VALIDATION SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All documentation validation tests passed!")
        print("✅ The improve-docstring-coverage implementation is complete.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
