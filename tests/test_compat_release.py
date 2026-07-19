from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from tests._root_contract import repository_root_for_test_file


STANDARD_ROOT = repository_root_for_test_file(__file__)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_std_001_old_compat_fixtures_decode_within_declared_window() -> None:
    window = _load_json(STANDARD_ROOT / "tests" / "compat" / "compat_window.json")

    assert window["task"] == "STD-001"
    assert window["currentVersion"] == (STANDARD_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert window["minReadableVersion"] == "1.1.0"
    fixture_versions = [fixture["version"] for fixture in window["fixtures"]]
    assert {"1.1.0", window["currentVersion"]} <= set(fixture_versions)
    for fixture in window["fixtures"]:
        fixture_path = STANDARD_ROOT / fixture["path"]
        payload = _load_json(fixture_path)
        assert payload["standardVersion"] == fixture["version"]
        assert {"standardVersion", "requiredArtifacts", "normativeArtifactRefs"} <= set(payload)


def test_std_001_release_report_links_sbom_changelog_and_verify_artifacts() -> None:
    report = _load_json(STANDARD_ROOT / "release" / "release_report.json")
    version = (STANDARD_ROOT / "VERSION").read_text(encoding="utf-8").strip()

    assert report["task"] == "STD-001"
    assert report["standardVersion"] == version
    assert report["compatibilityWindow"]["minReadableVersion"] == "1.1.0"
    assert version in report["compatibilityWindow"]["supportedVersions"]
    artifacts = report["artifacts"]
    for name in ("sbom", "changelog", "historicalFixture", "compatWindow"):
        artifact = artifacts[name]
        path = STANDARD_ROOT / artifact["path"]
        assert path.is_file(), f"STD-001 missing compatibility artifact: {artifact['path']}"
        assert artifact["sha256"] == _sha256(path)
    sbom = _load_json(STANDARD_ROOT / artifacts["sbom"]["path"])
    assert sbom["packages"][0]["name"] == "das-standard"
    changelog = (STANDARD_ROOT / artifacts["changelog"]["path"]).read_text(encoding="utf-8")
    assert version in changelog


def test_std_001_verify_gate_passes_with_compat_release_artifacts() -> None:
    proc = subprocess.run(
        ["bash", "scripts/verify", "--gate", "compat-release"],
        cwd=STANDARD_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "STD-001" in proc.stdout
    assert "compat-release" in proc.stdout


def test_std_001_verify_gate_names_missing_compatibility_artifact(tmp_path: Path) -> None:
    broken = tmp_path / "das-standard"
    shutil.copytree(
        STANDARD_ROOT,
        broken,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
    )
    missing = broken / "tests" / "compat" / "v1.4.0" / "standard_manifest.json"
    missing.unlink()

    proc = subprocess.run(
        ["bash", "scripts/verify", "--gate", "compat-release"],
        cwd=broken,
        capture_output=True,
        text=True,
        timeout=60,
    )

    output = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "STD-001" in output
    assert "tests/compat/v1.4.0/standard_manifest.json" in output


def test_std_001_release_snapshot_records_current_verify_digest() -> None:
    snapshot = _load_json(STANDARD_ROOT / "release_snapshot_manifest.json")
    verify_artifact = next(
        artifact for artifact in snapshot["artifacts"] if artifact["path"] == "scripts/verify"
    )

    expected = verify_artifact["sha256"]
    actual = _sha256(STANDARD_ROOT / "scripts" / "verify")
    assert expected == actual, (
        "STD-001 release snapshot hash mismatch for scripts/verify: "
        f"expected {expected} actual {actual}"
    )


def test_std_001_release_snapshot_gate_names_expected_and_actual_digest(tmp_path: Path) -> None:
    broken = tmp_path / "das-standard"
    shutil.copytree(
        STANDARD_ROOT,
        broken,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
    )
    snapshot_path = broken / "release_snapshot_manifest.json"
    snapshot = _load_json(snapshot_path)
    stale_digest = "0" * 64
    actual_digest = _sha256(broken / "scripts" / "verify")
    for artifact in snapshot["artifacts"]:
        if artifact["path"] == "scripts/verify":
            artifact["sha256"] = stale_digest
            break
    else:
        raise AssertionError("STD-001 release snapshot fixture missing scripts/verify")
    snapshot_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")

    proc = subprocess.run(
        ["bash", "scripts/verify", "--gate", "release-snapshot"],
        cwd=broken,
        capture_output=True,
        text=True,
        timeout=60,
    )

    output = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "scripts/verify" in output
    assert stale_digest in output
    assert actual_digest in output
