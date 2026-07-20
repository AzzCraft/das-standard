"""Shared test-root resolution helpers for release-package tests."""

from __future__ import annotations

from pathlib import Path


def repository_root_for_test_file(test_file: str | Path) -> Path:
    """Return the repository root that owns a test or docs_test file."""

    path = Path(test_file).resolve()
    for parent in path.parents:
        if parent.name in {"tests", "docs_tests"}:
            return parent.parent
    return path.parent


def release_package_root_for_workspace(root: str | Path) -> Path:
    """Return the embedded release package root for workspace or package runs."""

    path = Path(root).resolve()
    if path.name == "DAS_TOOLS_v1_0_0" and (path / "RELEASE_SHA256SUMS").is_file():
        return path
    return path / "DAS_TOOLS_v1_0_0"
