#!/usr/bin/env python3
"""Release self-conformance checks for the shipped DAS Standard bundle."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
VALID_GATES = {"all", "bundle-files", "schemas", "release-snapshot", "compat-release"}

def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def validate(data_rel: str, schema_rel: str) -> None:
    Draft202012Validator(load(schema_rel)).validate(load(data_rel))

def headings(text: str) -> list[tuple[int, int, str]]:
    result = []
    for index, line in enumerate(text.splitlines()):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            result.append((index, len(match.group(1)), match.group(2)))
    return result

def normalize(value: str) -> str:
    value = re.sub(r"\s+#+\s*$", "", value.strip())
    value = re.sub(r"^[0-9]+(?:\.[0-9]+)*\.?\s+", "", value)
    return re.sub(r"\s+", " ", value).strip().lower()

def slug(value: str) -> str:
    value = re.sub(r"[^\w\- ]", "", value.strip().lower())
    return re.sub(r"[\s-]+", "-", value).strip("-")

def section(text: str, title: str, by_slug: bool = False) -> str:
    lines = text.splitlines()
    if by_slug:
        marker = f'<a id="{title}"></a>'
        for index, line in enumerate(lines):
            if line.strip() == marker:
                return "\n".join(lines[index:])
    expected = title if by_slug else normalize(title)
    selected = None
    for index, level, heading in headings(text):
        candidate = slug(heading) if by_slug else normalize(heading)
        if candidate == expected:
            selected = index, level
            break
    if selected is None:
        raise AssertionError(f"missing section or anchor: {title}")
    start, level = selected
    end = next((index for index, other_level, _ in headings(text) if index > start and other_level <= level), len(lines))
    return "\n".join(lines[start:end])

def metadata_fields(text: str) -> set[str]:
    fields = set()
    for line in text.splitlines():
        match = re.match(r"^\s*-\s+(?:\*\*)?([^:*]+?)(?:\*\*)?:\s*", line)
        if match:
            fields.add(match.group(1).strip())
    return fields

def check_enum_definitions(manifest: dict) -> None:
    bindings = {
        "gateCadences": "gateCadenceDefinitions",
        "gateEnforcementClasses": "gateEnforcementDefinitions",
        "repoRoles": "repoRoleDefinitions",
        "toolClasses": "toolClassDefinitions",
        "toolPlacementTargets": "toolPlacementDefinitions",
        "verifyGateKinds": "verifyGateKindDefinitions",
        "moduleStates": "moduleStateDefinitions",
        "releaseSnapshotKinds": "releaseSnapshotKindDefinitions",
        "verifyReportOutcomes": "gateOutcomeDefinitions",
    }
    for enum_name, definitions_name in bindings.items():
        assert set(manifest["enums"][enum_name]) == set(manifest[definitions_name]), f"{definitions_name} must exactly define {enum_name}"

def check_templates(manifest: dict) -> None:
    catalog = load("template_catalog.json")["templates"]
    assert {item["docType"] for item in catalog} == set(manifest["docTypes"])
    assert len({item["docType"] for item in catalog}) == len(catalog)
    for item in catalog:
        path = ROOT / item["artifactPath"]
        assert path.is_file(), f"missing template artifact: {item['artifactPath']}"
        body = section(path.read_text(encoding="utf-8"), item["sectionAnchor"], by_slug=True)
        missing = set(manifest["requiredDocMetadata"][item["docType"]]) - metadata_fields(section(body, "Document Control"))
        assert not missing, f"template {item['docType']} missing metadata: {sorted(missing)}"
        present = {normalize(title) for _, _, title in headings(body)}
        missing = [
            name
            for name in manifest["requiredSections"][item["docType"]]
            if not any(actual == normalize(name) or actual.startswith(normalize(name) + " ") for actual in present)
        ]
        assert not missing, f"template {item['docType']} missing sections: {missing}"

def check_addenda(manifest: dict) -> None:
    for ref_name in ("deploymentAddendum", "governanceAddendum"):
        path = ROOT / manifest["normativeArtifactRefs"][ref_name]
        text = path.read_text(encoding="utf-8")
        missing = set(manifest["requiredDocMetadata"]["normative_addendum"]) - metadata_fields(section(text, "Document Control"))
        assert not missing, f"{path.name} missing metadata: {sorted(missing)}"
        present = {normalize(title) for _, _, title in headings(text)}
        missing = [name for name in manifest["requiredSections"]["normative_addendum"] if normalize(name) not in present]
        assert not missing, f"{path.name} missing sections: {missing}"

def check_ids_and_context(manifest: dict) -> None:
    chapters = {item["id"] for item in load("chapter_index.json")["chapters"]}
    clauses = {item["id"] for item in load("clause_index.json")["clauses"]}
    appendices = {f"A-{item['id'].split('-', 1)[1].upper()}" for item in load("chapter_index.json")["appendices"]}
    ids = load("ids/standard_ids.json")
    assert ids["standardVersion"] == manifest["standardVersion"]
    assert set(ids["appendixIds"]) == appendices
    contracts = load("context_packs/contracts-and-naming.json")["summary"].lower()
    assert "compatibility mode by default" in contracts and "refactor mode only" in contracts and "strict or tolerant" not in contracts
    evidence = load("context_packs/verification-and-evidence.json")
    assert evidence["chapters"] == ["ch-10"]
    assert "offline-first" not in evidence["summary"].lower() and "signing" not in evidence["summary"].lower()
    for path in (ROOT / "context_packs").glob("*.json"):
        pack = json.loads(path.read_text(encoding="utf-8"))
        assert pack["standardVersion"] == manifest["standardVersion"]
        assert set(pack["chapters"]) <= chapters
        assert set(pack["clauses"]) <= clauses

def check_snapshot_registry(manifest: dict) -> None:
    snapshot = load("release_snapshot_manifest.json")
    paths = {item["path"] for item in snapshot["artifacts"]}
    missing = sorted((set(manifest["requiredArtifacts"]) - {"release_snapshot_manifest.json"}) - paths)
    assert not missing, f"snapshot missing required artifacts: {missing}"
    registry = load("verify_registry.json")
    default = registry["defaultVerifyCommand"]
    actual = {item["command"].split()[-1] for item in registry["gates"] if item["command"].startswith(default + " --gate ")}
    assert actual == {"bundle-files", "schemas", "release-snapshot", "compat-release"}, f"registry gate mismatch: {sorted(actual)}"
    for item in snapshot["artifacts"]:
        path = ROOT / item["path"]
        assert path.is_file(), f"snapshot artifact missing: {item['path']}"
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual_hash == item["sha256"], f"snapshot hash mismatch: {item['path']}"
    joined = "\n".join(f"{item['path']}:{item['sha256']}" for item in sorted(snapshot["artifacts"], key=lambda value: value["path"]))
    assert hashlib.sha256(joined.encode()).hexdigest() == snapshot["bundleDigest"]

def check_compat(manifest: dict) -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    fixture = ROOT / "tests" / "compat" / f"v{version}" / "standard_manifest.json"
    assert fixture.is_file(), f"missing current compatibility fixture: {fixture.relative_to(ROOT)}"
    assert json.loads(fixture.read_text(encoding="utf-8")) == manifest, "current compatibility fixture must exactly copy the canonical manifest"

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", choices=sorted(VALID_GATES), default="all")
    args = parser.parse_args()
    manifest = load("standard_manifest.json")
    assert manifest["interactionProfiles"] == manifest["enums"]["interactionProfiles"]
    assert manifest["gateCadences"] == manifest["enums"]["gateCadences"]
    check_enum_definitions(manifest)
    if args.gate in {"all", "bundle-files"}:
        check_templates(manifest)
        check_addenda(manifest)
        check_ids_and_context(manifest)
    if args.gate in {"all", "schemas"}:
        for data, schema in (
            ("standard_manifest.example.json", "standard_manifest.schema.json"),
            ("chapter_index.json", "chapter_index.schema.json"),
            ("clause_index.json", "clause_index.schema.json"),
            ("ids/standard_ids.json", "standard_ids.schema.json"),
        ):
            validate(data, schema)
    if args.gate in {"all", "release-snapshot"}:
        check_snapshot_registry(manifest)
    if args.gate in {"all", "compat-release"}:
        check_compat(manifest)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
