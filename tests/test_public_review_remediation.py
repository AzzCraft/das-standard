import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError
from tests._root_contract import repository_root_for_test_file

ROOT = repository_root_for_test_file(__file__)
spec = importlib.util.spec_from_file_location("review_release_contract", ROOT / "tools/validate_release_contract.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


@pytest.mark.parametrize("defect", ["version", "missing", "duplicate", "unsupported-pin"])
def test_sbom_semantics_reject_even_when_outer_digests_are_recomputed(tmp_path, monkeypatch, defect):
    for name in ["requirements-verify.txt", "SBOM.spdx.json", "release_snapshot_manifest.json"]:
        shutil.copy2(ROOT / name, tmp_path / name)
    (tmp_path / "release").mkdir()
    shutil.copy2(ROOT / "release/release_report.json", tmp_path / "release/release_report.json")
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    validator.check_sbom_dependencies()
    path = tmp_path / "SBOM.spdx.json"
    sbom = json.loads(path.read_text())
    item = next(p for p in sbom["packages"] if p["name"] == "pytest")
    if defect == "version":
        item["versionInfo"] = "0.0.0"
    elif defect == "missing":
        sbom["packages"].remove(item)
    elif defect == "duplicate":
        sbom["packages"].append(dict(item))
    else:
        (tmp_path / "requirements-verify.txt").write_text("pytest>=9\n")
    path.write_text(json.dumps(sbom))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    report_path = tmp_path / "release/release_report.json"
    report = json.loads(report_path.read_text())
    report["artifacts"]["sbom"]["sha256"] = digest
    report_path.write_text(json.dumps(report))
    snapshot_path = tmp_path / "release_snapshot_manifest.json"
    snapshot = json.loads(snapshot_path.read_text())
    for row in snapshot["artifacts"]:
        if row["path"] in {"SBOM.spdx.json", "requirements-verify.txt", "release/release_report.json"}:
            row["sha256"] = hashlib.sha256((tmp_path / row["path"]).read_bytes()).hexdigest()
    joined = "\n".join(f"{r['path']}:{r['sha256']}" for r in sorted(snapshot["artifacts"], key=lambda r: r["path"]))
    snapshot["bundleDigest"] = hashlib.sha256(joined.encode()).hexdigest()
    snapshot_path.write_text(json.dumps(snapshot))
    with pytest.raises(ValueError):
        validator.check_sbom_dependencies()


def test_actual_manifest_helper_rejects_wrong_structure_and_version(tmp_path, monkeypatch):
    for name in ["VERSION", "standard_manifest.json", "standard_manifest.schema.json", "tooling_lock.schema.json"]:
        shutil.copy2(ROOT / name, tmp_path / name)
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    validator.check_manifest_artifacts()
    path = tmp_path / "standard_manifest.json"
    original = json.loads(path.read_text())
    for payload in [{"standardVersion": "0.0.0", "unrelatedNote": "1.5.0-beta.1"}, {**original, "standardVersion": "0.0.0"}]:
        path.write_text(json.dumps(payload))
        with pytest.raises((ValueError, ValidationError)):
            validator.check_manifest_artifacts()
    path.write_text(json.dumps(original))
    (tmp_path / "tooling_lock.json").write_text("{}")
    with pytest.raises(ValidationError):
        validator.check_manifest_artifacts()


def test_all_edition_author_fragments_exist_and_missing_fragment_rejects(tmp_path, monkeypatch):
    validator.check_author_links()
    (tmp_path / "modules").mkdir()
    for name in ["modules/requirements.md", "modules/edition-1.5.md", "standard_requirements.json"]:
        shutil.copy2(ROOT / name, tmp_path / name)
    path = tmp_path / "modules/edition-1.5.md"
    path.write_text(path.read_text().replace('<a id="shared-contracts"></a>', ''))
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="unresolved normative author"):
        validator.check_author_links()


def test_diff_helper_parses_supported_calls_and_propagates_git_errors(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copy2(ROOT / "scripts/diff_standard", scripts / "diff_standard")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "SPECIFICATION.md").write_text("old\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "SPECIFICATION.md"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "-qm", "fixture"], check=True)
    for args in [["HEAD"], ["HEAD", "HEAD"], ["HEAD", "--stat"], ["HEAD", "HEAD", "--stat"]]:
        run = subprocess.run(["bash", str(scripts / "diff_standard"), *args], capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
    for args in [["HEAD", "nonexistent-ref"], ["--bad"], ["HEAD", "HEAD", "extra"]]:
        run = subprocess.run(["bash", str(scripts / "diff_standard"), *args], capture_output=True, text=True)
        assert run.returncode != 0
