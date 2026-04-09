"""Test standard manifest and schema validation."""

import json
import unittest
from pathlib import Path

STANDARD_ROOT = Path(__file__).resolve().parents[1]


class TestManifest(unittest.TestCase):
    """Validate standard_manifest.json if present."""

    def test_manifest_loads(self):
        path = STANDARD_ROOT / "standard_manifest.json"
        if not path.exists():
            self.skipTest("standard_manifest.json not found")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("standardId", data)


class TestVersionTrace(unittest.TestCase):
    """Validate VERSION appears in CHANGELOG."""

    def test_version_in_changelog(self):
        version_path = STANDARD_ROOT / "VERSION"
        changelog_path = STANDARD_ROOT / "CHANGELOG.md"
        if not version_path.exists() or not changelog_path.exists():
            self.skipTest("VERSION or CHANGELOG.md not found")
        version = version_path.read_text().strip()
        changelog = changelog_path.read_text()
        self.assertIn(version, changelog)


class TestSpecificationExists(unittest.TestCase):
    """Check SPECIFICATION.md exists."""

    def test_spec_exists(self):
        self.assertTrue((STANDARD_ROOT / "SPECIFICATION.md").exists())


if __name__ == "__main__":
    unittest.main()
