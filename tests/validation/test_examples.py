"""Validation tests for sitq runnable examples.

This test module executes example scripts to ensure they remain runnable
and function correctly. Each example is run with a timeout to prevent
hangs.
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple

import pytest


def get_example_scripts() -> List[Tuple[str, str]]:
    """Get list of example scripts to validate.

    Returns:
        List of (script_name, description) tuples.
    """
    examples_dir = Path(__file__).parent.parent.parent / "examples" / "basic"

    examples = [
        ("01_end_to_end.py", "End-to-end workflow"),
        ("02_eta_delayed_execution.py", "Delayed execution with ETA"),
        ("03_bounded_concurrency.py", "Bounded concurrency control"),
        ("04_failures_and_tracebacks.py", "Failure handling and tracebacks"),
        ("05_sync_client_with_worker.py", "Sync client with async worker"),
    ]

    return [
        (str(examples_dir / script), description)
        for script, description in examples
        if (examples_dir / script).exists()
    ]


def run_example(script_path: str, timeout: int = 35) -> Tuple[bool, str, str]:
    """Run an example script and capture output.

    Args:
        script_path: Path to the example script.
        timeout: Maximum time to allow the script to run (seconds).

    Returns:
        Tuple of (success: bool, stdout: str, stderr: str).
    """
    start_time = time.time()

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            timeout=timeout,
            capture_output=True,
            text=True,
        )

        elapsed = time.time() - start_time
        success = result.returncode == 0

        return success, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        return False, "", f"Script timed out after {elapsed:.1f}s (limit: {timeout}s)"
    except Exception as e:
        elapsed = time.time() - start_time
        return False, "", f"Script failed with exception: {e}"


@pytest.mark.parametrize("script_path,description", get_example_scripts())
def test_example_runs(script_path: str, description: str):
    """Test that each example script runs successfully.

    This test executes the example script with a timeout and verifies
    that it completes without errors. Examples should complete within
    30 seconds per the design requirements.
    """
    success, stdout, stderr = run_example(script_path)

    if not success:
        pytest.fail(
            f"Example '{description}' failed:\n"
            f"  Script: {Path(script_path).name}\n"
            f"  Stderr: {stderr}\n"
            f"  Stdout: {stdout}"
        )


def test_all_examples_exist():
    """Verify all expected example scripts exist."""
    examples_dir = Path(__file__).parent.parent.parent / "examples" / "basic"

    expected = [
        "01_end_to_end.py",
        "02_eta_delayed_execution.py",
        "03_bounded_concurrency.py",
        "04_failures_and_tracebacks.py",
        "05_sync_client_with_worker.py",
    ]

    for example in expected:
        example_path = examples_dir / example
        assert example_path.exists(), (
            f"Expected example {example} not found at {example_path}"
        )


def test_examples_complete_quickly():
    """Verify examples complete within reasonable time."""
    scripts = get_example_scripts()

    for script_path, description in scripts:
        success, stdout, stderr = run_example(script_path, timeout=35)

        if not success and "timed out" in stderr:
            pytest.fail(
                f"Example '{description}' took too long to complete.\n"
                f"  Script: {Path(script_path).name}\n"
                f"  Error: {stderr}\n"
                f"  Examples should complete within 30 seconds per design requirements."
            )


def test_example_outputs():
    """Verify examples produce expected output patterns."""
    scripts = get_example_scripts()

    for script_path, description in scripts:
        success, stdout, stderr = run_example(script_path)

        if not success:
            continue

        script_name = Path(script_path).name

        # Check for expected completion marker
        if "Example Complete" not in stdout and "Example Complete" not in stderr:
            pytest.fail(
                f"Example '{description}' did not produce expected completion marker.\n"
                f"  Script: {script_name}\n"
                f"  Expected output to contain 'Example Complete'"
            )
