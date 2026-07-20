from __future__ import annotations

import json
import subprocess

from tests._root_contract import repository_root_for_test_file


ROOT = repository_root_for_test_file(__file__)


def _load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_current_compat_fixture_is_the_canonical_manifest_copy() -> None:
    manifest = _load("standard_manifest.json")
    fixture = _load("tests/compat/v1.4.0/standard_manifest.json")
    assert fixture == manifest


def test_release_contract_validator_checks_governed_template_surface() -> None:
    proc = subprocess.run(
        ["python3", "tools/validate_release_contract.py", "--gate", "bundle-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_verify_registry_matches_the_four_implemented_gates() -> None:
    registry = _load("verify_registry.json")
    default = registry["defaultVerifyCommand"]
    gates = {
        item["command"].split()[-1]
        for item in registry["gates"]
        if item["command"].startswith(default + " --gate ")
    }
    assert gates == {"bundle-files", "schemas", "release-snapshot", "compat-release"}
