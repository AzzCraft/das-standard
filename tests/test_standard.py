"""Test standard manifest and schema validation."""

import json
import unittest
from pathlib import Path
from tests._root_contract import repository_root_for_test_file

STANDARD_ROOT = repository_root_for_test_file(__file__)


class TestManifest(unittest.TestCase):
    """Validate the required standard manifest."""

    def test_manifest_loads(self):
        path = STANDARD_ROOT / "standard_manifest.json"
        self.assertTrue(path.is_file(), "standard_manifest.json not found")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("standardId", data)


class TestVersionTrace(unittest.TestCase):
    """Validate VERSION appears in CHANGELOG."""

    def test_version_in_changelog(self):
        version_path = STANDARD_ROOT / "VERSION"
        changelog_path = STANDARD_ROOT / "CHANGELOG.md"
        self.assertTrue(version_path.is_file() and changelog_path.is_file(), "VERSION or CHANGELOG.md not found")
        version = version_path.read_text().strip()
        changelog = changelog_path.read_text()
        self.assertIn(version, changelog)


class TestSpecificationExists(unittest.TestCase):
    """Check SPECIFICATION.md exists."""

    def test_spec_exists(self):
        self.assertTrue((STANDARD_ROOT / "SPECIFICATION.md").exists())


if __name__ == "__main__":
    unittest.main()
