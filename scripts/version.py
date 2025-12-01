#!/usr/bin/env python3
"""
Version management script for sitq documentation.

This script handles:
- Version bumping
- Changelog updates
- Documentation versioning
- Release preparation
"""

import re
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


def get_current_version() -> str:
    """Get current version from sitq.__init__.py."""
    init_file = Path("src/sitq/__init__.py")

    if not init_file.exists():
        raise FileNotFoundError(f"Could not find {init_file}")

    content = init_file.read_text()
    match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)

    if not match:
        raise ValueError("Could not find version in __init__.py")

    return match.group(1)


def update_version(new_version: str) -> None:
    """Update version in sitq.__init__.py."""
    init_file = Path("src/sitq/__init__.py")
    content = init_file.read_text()

    # Update version
    content = re.sub(
        r'__version__ = ["\'][^"\']+["\']', f'__version__ = "{new_version}"', content
    )

    init_file.write_text(content)
    print(f"Updated version to {new_version}")


def parse_version(version: str) -> Tuple[int, int, int]:
    """Parse semantic version string."""
    match = re.match(r"(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")

    return tuple(map(int, match.groups()))


def bump_version(current: str, bump_type: str) -> str:
    """Bump version based on type."""
    major, minor, patch = parse_version(current)

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


def update_changelog(version: str, changes: List[str]) -> None:
    """Update changelog with new version."""
    changelog_file = Path("docs/user-guide/changelog.md")

    if not changelog_file.exists():
        raise FileNotFoundError(f"Could not find {changelog_file}")

    content = changelog_file.read_text()

    # Find unreleased section
    unreleased_match = re.search(r"## \[Unreleased\]", content)
    if not unreleased_match:
        raise ValueError("Could not find [Unreleased] section in changelog")

    # Create new version section
    today = datetime.now().strftime("%Y-%m-%d")
    new_section = f"## [{version}] - {today}\n\n"

    # Add changes
    if changes:
        new_section += "### Added\n"
        for change in changes:
            new_section += f"- {change}\n"
        new_section += "\n"

    # Replace unreleased section
    content = content.replace(
        "## [Unreleased]",
        f"## [Unreleased]\n\n### Added\n\n{new_section}## [Unreleased]",
    )

    changelog_file.write_text(content)
    print(f"Updated changelog for version {version}")


def update_mkdocs_version(version: str) -> None:
    """Update version in mkdocs configuration."""
    mkdocs_file = Path("docs/mkdocs.yml")

    if not mkdocs_file.exists():
        raise FileNotFoundError(f"Could not find {mkdocs_file}")

    content = mkdocs_file.read_text()

    # Update version in site description
    content = re.sub(
        r"site_description: Simple Task Queue for Python",
        f"site_description: Simple Task Queue for Python v{version}",
        content,
    )

    mkdocs_file.write_text(content)
    print(f"Updated mkdocs version to {version}")


def create_version_branch(version: str) -> None:
    """Create version branch for documentation."""
    import subprocess

    branch_name = f"version-{version}"

    try:
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        print(f"Created branch {branch_name}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create branch: {e}")


def tag_version(version: str) -> None:
    """Create git tag for version."""
    import subprocess

    try:
        subprocess.run(
            ["git", "tag", "-a", f"v{version}", "-m", f"Release v{version}"], check=True
        )
        print(f"Created tag v{version}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create tag: {e}")


def prepare_release(bump_type: str, changes: List[str]) -> None:
    """Prepare a new release."""
    print(f"Preparing {bump_type} release...")

    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")

    # Calculate new version
    new_version = bump_version(current_version, bump_type)
    print(f"New version: {new_version}")

    # Update version in code
    update_version(new_version)

    # Update changelog
    update_changelog(new_version, changes)

    # Update mkdocs configuration
    update_mkdocs_version(new_version)

    print(f"Release {new_version} prepared successfully!")
    print("Don't forget to:")
    print("1. Review the changes")
    print("2. Commit the changes")
    print("3. Create a pull request")
    print("4. Tag the release after merge")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Version management for sitq")
    parser.add_argument(
        "command", choices=["current", "bump", "prepare"], help="Command to execute"
    )
    parser.add_argument(
        "--type", choices=["major", "minor", "patch"], help="Type of version bump"
    )
    parser.add_argument("--changes", nargs="*", help="List of changes for changelog")

    args = parser.parse_args()

    try:
        if args.command == "current":
            version = get_current_version()
            print(f"Current version: {version}")

        elif args.command == "bump":
            if not args.type:
                print("Error: --type is required for bump command")
                sys.exit(1)

            current_version = get_current_version()
            new_version = bump_version(current_version, args.type)
            print(f"Bumped version: {current_version} -> {new_version}")

        elif args.command == "prepare":
            if not args.type:
                print("Error: --type is required for prepare command")
                sys.exit(1)

            changes = args.changes or []
            prepare_release(args.type, changes)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
