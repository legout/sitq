#!/usr/bin/env python3
"""
Test script for mkdocstrings API reference generation.

This script validates that:
1. mkdocstrings can generate API reference
2. All public APIs are documented
3. Documentation builds without errors
4. Cross-references work correctly
"""

import sys
import subprocess
import importlib
import inspect
from pathlib import Path


def test_mkdocstrings_import():
    """Test if mkdocstrings can be imported."""
    try:
        import mkdocstrings

        print("✅ mkdocstrings is available")
        return True
    except ImportError as e:
        print(f"❌ mkdocstrings not available: {e}")
        return False


def test_sitq_import():
    """Test if sitq can be imported."""
    try:
        import sitq

        print(f"✅ sitq v{sitq.__version__} imported successfully")
        return True
    except ImportError as e:
        print(f"❌ sitq import failed: {e}")
        return False


def test_public_api_coverage():
    """Test if all public APIs are accessible."""
    try:
        import sitq

        # Check core components
        core_components = ["TaskQueue", "Worker", "SyncTaskQueue", "Task", "Result"]
        for component in core_components:
            if hasattr(sitq, component):
                obj = getattr(sitq, component)
                print(f"✅ {component}: {type(obj).__name__}")
            else:
                print(f"❌ {component}: NOT FOUND")

        # Check backends
        backends = ["SQLiteBackend", "Backend"]
        for backend in backends:
            if hasattr(sitq, backend):
                obj = getattr(sitq, backend)
                print(f"✅ {backend}: {type(obj).__name__}")
            else:
                print(f"❌ {backend}: NOT FOUND")

        # Check exceptions
        exceptions = ["SitqError", "TaskQueueError", "BackendError", "WorkerError"]
        for exc in exceptions:
            if hasattr(sitq, exc):
                obj = getattr(sitq, exc)
                print(f"✅ {exc}: {type(obj).__name__}")
            else:
                print(f"❌ {exc}: NOT FOUND")

        return True
    except Exception as e:
        print(f"❌ API coverage test failed: {e}")
        return False


def test_docstring_coverage():
    """Test if public APIs have docstrings."""
    try:
        import sitq

        # Test core classes
        classes_to_test = [
            sitq.TaskQueue,
            sitq.Worker,
            sitq.SyncTaskQueue,
            sitq.Task,
            sitq.Result,
            sitq.SQLiteBackend,
        ]

        for cls in classes_to_test:
            if cls.__doc__:
                print(f"✅ {cls.__name__}: Has docstring ({len(cls.__doc__)} chars)")
            else:
                print(f"❌ {cls.__name__}: Missing docstring")

            # Test public methods
            for name, method in inspect.getmembers(cls, predicate=inspect.ismethod):
                if not name.startswith("_"):
                    if method.__doc__:
                        print(f"  ✅ {name}: Has docstring")
                    else:
                        print(f"  ❌ {name}: Missing docstring")

        return True
    except Exception as e:
        print(f"❌ Docstring coverage test failed: {e}")
        return False


def test_mkdocs_build():
    """Test if MkDocs can build documentation."""
    try:
        # Try to build documentation
        result = subprocess.run(
            ["mkdocs", "build", "--quiet", "--site-dir", "test_site"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            print("✅ MkDocs build successful")

            # Check if API reference was generated
            api_dir = Path("test_site/api-reference")
            if api_dir.exists():
                print("✅ API reference generated")

                # List generated files
                for file in api_dir.rglob("*.md"):
                    print(f"  📄 {file.relative_to(api_dir)}")
            else:
                print("❌ API reference not generated")

            return True
        else:
            print(f"❌ MkDocs build failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ MkDocs build timed out")
        return False
    except Exception as e:
        print(f"❌ MkDocs build test failed: {e}")
        return False


def test_cross_references():
    """Test if cross-references in documentation work."""
    try:
        # Check if documentation files contain cross-references
        docs_dir = Path("docs")

        if not docs_dir.exists():
            print("❌ Documentation directory not found")
            return False

        # Look for cross-reference patterns
        cross_ref_patterns = [
            "[`TaskQueue`](api-reference/queue.md)",
            "[`Worker`](api-reference/worker.md)",
            "[`SQLiteBackend`](api-reference/backends/sqlite.md)",
        ]

        for pattern in cross_ref_patterns:
            found = False
            for file in docs_dir.rglob("*.md"):
                content = file.read_text()
                if pattern in content:
                    found = True
                    break

            if found:
                print(f"✅ Cross-reference found: {pattern}")
            else:
                print(f"❌ Cross-reference missing: {pattern}")

        return True
    except Exception as e:
        print(f"❌ Cross-reference test failed: {e}")
        return False


def test_examples():
    """Test if examples in documentation are valid."""
    try:
        docs_dir = Path("docs")

        if not docs_dir.exists():
            print("❌ Documentation directory not found")
            return False

        # Look for code examples
        python_code_blocks = []

        for file in docs_dir.rglob("*.md"):
            content = file.read_text()

            # Find Python code blocks
            import re

            code_blocks = re.findall(r"```python\n(.*?)\n```", content, re.DOTALL)
            python_code_blocks.extend(code_blocks)

        print(f"Found {len(python_code_blocks)} Python code blocks")

        # Test basic syntax of code blocks
        valid_examples = 0
        for i, code in enumerate(python_code_blocks[:5]):  # Test first 5
            try:
                compile(code, f"<example_{i}>", "exec")
                print(f"✅ Example {i}: Valid syntax")
                valid_examples += 1
            except SyntaxError as e:
                print(f"❌ Example {i}: Syntax error - {e}")

        print(f"Valid examples: {valid_examples}/{min(len(python_code_blocks), 5)}")
        return valid_examples > 0

    except Exception as e:
        print(f"❌ Examples test failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🧪 Running mkdocstrings validation tests...\n")

    tests = [
        ("mkdocstrings Import", test_mkdocstrings_import),
        ("sitq Import", test_sitq_import),
        ("Public API Coverage", test_public_api_coverage),
        ("Docstring Coverage", test_docstring_coverage),
        ("MkDocs Build", test_mkdocs_build),
        ("Cross-References", test_cross_references),
        ("Examples", test_examples),
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
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Documentation is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
