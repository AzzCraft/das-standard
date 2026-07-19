#!/usr/bin/env python3
"""Generate the non-circular standard content manifest checked into the repo."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "release_snapshot_manifest.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    manifest = json.loads((ROOT / "standard_manifest.json").read_text(encoding="utf-8"))
    artifacts = []
    for rel in sorted(set(manifest["requiredArtifacts"]) - {OUTPUT.name}):
        path = ROOT / rel
        if not path.is_file():
            raise SystemExit(f"required content is not a file: {rel}")
        if rel.startswith(".github/"):
            artifact_class = "ci"
        elif rel.startswith("scripts/"):
            artifact_class = "script"
        elif rel.endswith(".schema.json"):
            artifact_class = "schema"
        elif ".example." in rel or rel.startswith("examples/"):
            artifact_class = "example"
        elif rel.endswith(".md"):
            artifact_class = "normative"
        else:
            artifact_class = "supporting"
        artifacts.append({"path": rel, "sha256": sha(path), "artifactClass": artifact_class, "required": True})
    joined = "\n".join(f"{item['path']}:{item['sha256']}" for item in artifacts)
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    return {
        "$schema": "./release_snapshot_manifest.schema.json",
        "schemaVersion": "1.0.0",
        "standardVersion": version,
        "standardManifestVersion": version,
        "snapshotKind": "standard_content_bundle",
        "createdAt": "2026-07-19T00:00:00Z",
        "buildRef": f"content:v{version}",
        "sourceRepoRef": {
            "kind": "custom", "uri": "content-manifest://das-standard",
            "pinType": "version", "pinValue": version, "floating": False,
        },
        "bundleDigestAlgorithm": "sha256",
        "bundleDigest": hashlib.sha256(joined.encode()).hexdigest(),
        "artifacts": artifacts,
        "mirrorRules": {
            "localMirrorAllowed": True,
            "requireSnapshotRefForMirror": True,
            "allowLocalModifications": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(build(), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != rendered:
            raise SystemExit("release_snapshot_manifest.json is stale")
    else:
        OUTPUT.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
