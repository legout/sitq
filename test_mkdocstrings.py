#!/usr/bin/env python3
"""Test script to verify mkdocstrings can generate API reference."""

import subprocess
import sys
import os


def test_mkdocstrings():
    """Test if mkdocstrings can process sitq source code."""

    print("Testing mkdocstrings API generation...")

    # Change to src directory
    os.chdir("src")

    try:
        # Try to run mkdocstrings on sitq module
        result = subprocess.run(
            ["python", "-m", "mkdocstrings", "sitq", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("✅ mkdocstrings successfully processed sitq module")
            print("Output preview:")
            print(
                result.stdout[:500] + "..."
                if len(result.stdout) > 500
                else result.stdout
            )
            return True
        else:
            print("❌ mkdocstrings failed to process sitq module")
            print("Error output:")
            print(result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("❌ mkdocstrings timed out after 30 seconds")
        return False
    except FileNotFoundError:
        print("❌ mkdocstrings not found - install with: pip install mkdocstrings")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = test_mkdocstrings()
    sys.exit(0 if success else 1)
