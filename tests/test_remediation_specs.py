"""Remediation spec tests for das-standard (STD-001)."""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from tests._root_contract import repository_root_for_test_file


ROOT = repository_root_for_test_file(__file__)


class StandardRemediationSpecTests(unittest.TestCase):

    # --- STD-001: machine-readable artifacts exist ---
    def test_std_001_machine_readable_artifacts_exist(self) -> None:
        for rel in (
            "standard_manifest.json",
            "chapter_index.json",
            "clause_index.json",
            "verify_registry.json",
            "context_packs",
        ):
            with self.subTest(file=rel):
                self.assertTrue((ROOT / rel).exists(), f"{rel} missing")

    def test_std_001_standard_manifest_is_valid_json(self) -> None:
        manifest = json.loads((ROOT / "standard_manifest.json").read_text(encoding="utf-8"))
        self.assertIn("standardId", manifest)
        self.assertIn("standardVersion", manifest)

    def test_std_001_verify_script_exists(self) -> None:
        self.assertTrue((ROOT / "scripts" / "verify").exists())

    # --- STD-001 deep: chapter_index.json is valid JSON array ---
    def test_std_001_chapter_index_valid(self) -> None:
        data = json.loads((ROOT / "chapter_index.json").read_text(encoding="utf-8"))
        self.assertIsInstance(data, (list, dict))
        if isinstance(data, list):
            self.assertGreater(len(data), 0, "chapter_index.json is empty")

    # --- STD-001 deep: clause_index.json is valid JSON ---
    def test_std_001_clause_index_valid(self) -> None:
        data = json.loads((ROOT / "clause_index.json").read_text(encoding="utf-8"))
        self.assertIsInstance(data, (list, dict))

    # --- STD-001 deep: verify_registry.json is valid JSON ---
    def test_std_001_verify_registry_valid(self) -> None:
        data = json.loads((ROOT / "verify_registry.json").read_text(encoding="utf-8"))
        self.assertIsInstance(data, (list, dict))

    # --- STD-001 deep: context_packs dir has at least one .json ---
    def test_std_001_context_packs_has_json(self) -> None:
        cp = ROOT / "context_packs"
        self.assertTrue(cp.is_dir())
        jsons = list(cp.glob("*.json"))
        self.assertGreater(len(jsons), 0, "context_packs has no .json files")

    # --- STD-001 deep: verify script checks artifacts ---
    def test_std_001_verify_script_checks_artifacts(self) -> None:
        text = (ROOT / "scripts" / "verify").read_text(encoding="utf-8")
        self.assertIn("standard_manifest.json", text)
        self.assertIn("requiredArtifacts", text)

    # --- STD-001 deep: standard_manifest has requiredArtifacts list ---
    def test_std_001_manifest_has_required_artifacts(self) -> None:
        manifest = json.loads((ROOT / "standard_manifest.json").read_text(encoding="utf-8"))
        self.assertIn("requiredArtifacts", manifest)
        self.assertIsInstance(manifest["requiredArtifacts"], list)
        self.assertGreater(len(manifest["requiredArtifacts"]), 0)

    # --- STD-001 deep: all requiredArtifacts actually exist ---
    def test_std_001_all_required_artifacts_exist(self) -> None:
        manifest = json.loads((ROOT / "standard_manifest.json").read_text(encoding="utf-8"))
        for rel in manifest.get("requiredArtifacts", []):
            with self.subTest(artifact=rel):
                self.assertTrue((ROOT / rel).exists(), f"Missing: {rel}")

    # --- STD-001 deep: schema files exist ---
    def test_std_001_schema_files_exist(self) -> None:
        for name in ("standard_manifest.schema.json", "verify_registry.schema.json"):
            with self.subTest(schema=name):
                self.assertTrue((ROOT / name).exists(), f"Missing: {name}")

    # --- STD-001 deep: release_snapshot_manifest exists ---
    def test_std_001_release_snapshot_manifest_exists(self) -> None:
        self.assertTrue((ROOT / "release_snapshot_manifest.json").exists())

    # --- STD-001 deep: release_snapshot has bundleDigest ---
    def test_std_001_release_snapshot_has_bundle_digest(self) -> None:
        data = json.loads((ROOT / "release_snapshot_manifest.json").read_text(encoding="utf-8"))
        self.assertIn("bundleDigest", data)
        self.assertIn("artifacts", data)
        self.assertGreater(len(data["artifacts"]), 0)

    # --- STD-001 deep: verify_registry has gates ---
    def test_std_001_verify_registry_has_gates(self) -> None:
        data = json.loads((ROOT / "verify_registry.json").read_text(encoding="utf-8"))
        self.assertIn("gates", data)
        self.assertIsInstance(data["gates"], list)
        self.assertGreater(len(data["gates"]), 0)

    # --- V9 Item 01: das-standard is DAS v1.4.0+ canonical release repo ---

    def test_v9_01_version_at_least_140(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        parts = tuple(int(x) for x in version.split("."))
        self.assertGreaterEqual(parts, (1, 4, 0), f"VERSION is too old: {version}")

    def test_indexes_cover_every_numbered_spec_heading(self) -> None:
        spec = (ROOT / "SPECIFICATION.md").read_text(encoding="utf-8")
        chapter_index = json.loads((ROOT / "chapter_index.json").read_text(encoding="utf-8"))
        clause_index = json.loads((ROOT / "clause_index.json").read_text(encoding="utf-8"))
        expected_chapters = {
            line.split(".", 1)[0].removeprefix("## ")
            for line in spec.splitlines()
            if line.startswith("## ") and line[3:4].isdigit()
        }
        expected_clauses = {
            line.split(" ", 2)[1]
            for line in spec.splitlines()
            if line.startswith("### ") and line[4:5].isdigit()
        }
        actual_chapters = {item["id"].removeprefix("ch-") for item in chapter_index["chapters"]}
        actual_clauses = {item["id"].removeprefix("cl-") for item in clause_index["clauses"]}
        self.assertEqual(actual_chapters, expected_chapters)
        self.assertEqual(actual_clauses, expected_clauses)

    def test_v9_01_specification_exists(self) -> None:
        self.assertTrue((ROOT / "SPECIFICATION.md").exists())

    def test_v9_01_workflows_exist(self) -> None:
        self.assertTrue((ROOT / ".github" / "workflows" / "verify.yml").exists())
        self.assertTrue((ROOT / ".github" / "workflows" / "release.yml").exists())

    def test_v9_01_appendix_m_exists(self) -> None:
        matches = list((ROOT / "appendices").glob("appendix-m-*"))
        self.assertGreater(len(matches), 0, "Appendix M missing")

    def test_v9_01_appendix_n_exists(self) -> None:
        matches = list((ROOT / "appendices").glob("appendix-n-*"))
        self.assertGreater(len(matches), 0, "Appendix N missing")

    def test_v9_01_closure_schema_files_exist(self) -> None:
        for name in (
            "suite_version_closure.schema.json",
            "suite_version_closure.example.json",
            "tooling_lock.schema.json",
            "tooling_lock.example.json",
            "local_extension_manifest.schema.json",
            "local_extension_manifest.example.json",
            "template_catalog.json",
            "template_catalog.schema.json",
            "verify_report.schema.json",
            "release_snapshot_manifest.schema.json",
        ):
            with self.subTest(file=name):
                self.assertTrue((ROOT / name).exists(), f"missing: {name}")

    # --- STD-001 deep: standard_manifest has normativeArtifactRefs ---
    def test_std_001_manifest_has_normative_refs(self) -> None:
        manifest = json.loads((ROOT / "standard_manifest.json").read_text(encoding="utf-8"))
        self.assertIn("normativeArtifactRefs", manifest)
        self.assertIsInstance(manifest["normativeArtifactRefs"], dict)
        self.assertGreater(len(manifest["normativeArtifactRefs"]), 0)

    # --- Additional Item 01 content-validation tests ---

    def test_v9_01_version_matches_manifest(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        manifest = json.loads((ROOT / "standard_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["standardVersion"], version)

    def test_v9_01_schema_files_are_valid_json_schema(self) -> None:
        for f in ROOT.glob("*.schema.json"):
            with self.subTest(schema=f.name):
                data = json.loads(f.read_text(encoding="utf-8"))
                self.assertIsInstance(data, dict)
                self.assertTrue(
                    "$schema" in data or "type" in data or "properties" in data,
                    f"{f.name} does not look like a JSON Schema",
                )

    def test_v9_01_example_validates_against_schema(self) -> None:
        pairs = [
            ("suite_version_closure.example.json", "suite_version_closure.schema.json"),
            ("tooling_lock.example.json", "tooling_lock.schema.json"),
            ("local_extension_manifest.example.json", "local_extension_manifest.schema.json"),
        ]
        for example_name, schema_name in pairs:
            example_path = ROOT / example_name
            schema_path = ROOT / schema_name
            if not example_path.exists() or not schema_path.exists():
                continue
            with self.subTest(example=example_name):
                example = json.loads(example_path.read_text(encoding="utf-8"))
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                for req in schema.get("required", []):
                    self.assertIn(req, example, f"{example_name} missing required field: {req}")

    def test_v9_01_changelog_mentions_current_version(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(version, changelog, "CHANGELOG.md does not mention current VERSION")

    def test_v9_01_no_placeholder_in_manifest(self) -> None:
        text = (ROOT / "standard_manifest.json").read_text(encoding="utf-8")
        for marker in ("TODO", "PLACEHOLDER", "TBD", "FIXME"):
            self.assertNotIn(marker, text)

    def test_v9_01_release_snapshot_artifacts_all_exist(self) -> None:
        data = json.loads((ROOT / "release_snapshot_manifest.json").read_text(encoding="utf-8"))
        for entry in data.get("artifacts", []):
            rel = entry if isinstance(entry, str) else entry.get("path", entry.get("name", ""))
            if rel:
                with self.subTest(artifact=rel):
                    self.assertTrue((ROOT / rel).exists(), f"Snapshot artifact missing: {rel}")


if __name__ == "__main__":
    unittest.main()
