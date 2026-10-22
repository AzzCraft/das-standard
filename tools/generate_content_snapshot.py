#!/usr/bin/env python3
"""Generate the non-circular standard content manifest checked into the repo."""
from __future__ import annotations

# Direct CLI use has the same dependency isolation as scripts/verify.
import sys
if __name__ == "__main__" and not sys.flags.isolated:
    import os
    os.execv(sys.executable, [sys.executable, "-I", "-B", __file__, *sys.argv[1:]])

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import zipfile

# Resolve the adjacent helper explicitly; these maintenance scripts support -I.
import importlib.util
_io_spec = importlib.util.spec_from_file_location("das_standard_io", Path(__file__).with_name("standard_io.py"))
standard_io = importlib.util.module_from_spec(_io_spec)
_io_spec.loader.exec_module(standard_io)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "release_snapshot_manifest.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    manifest = standard_io.loads((ROOT / "standard_manifest.json").read_text(encoding="utf-8"))
    standard_io.validate_content_inventory(ROOT, manifest)
    artifacts = []
    for rel in sorted(set(manifest["requiredArtifacts"]) - {OUTPUT.name}):
        if (not isinstance(rel, str) or not rel or Path(rel).is_absolute()
                or Path(rel).as_posix() != rel or any(p in ('', '.', '..') for p in rel.split('/'))
                or '\\' in rel):
            raise SystemExit(f"unsafe required content path: {rel}")
        path = ROOT / rel
        if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)):
            raise SystemExit(f"required content is not a regular local file: {rel}")
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
        # A stable content declaration, never a claim about a platform publish
        # event. The actual release receipt remains outside the payload.
        "createdAt": manifest['releasedAt'] + "T00:00:00Z",
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


def _output_parent(destination: Path) -> int:
    """Open the caller's existing output directory without following aliases."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open('/', flags)
    try:
        for part in destination.parent.parts[1:]:
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except OSError as exc:
        os.close(fd)
        raise SystemExit('content archive output parent must be an existing directory without links') from exc


def archive(destination: Path, rendered: str) -> None:
    """Package the checked content profile; no approval or source-tar alias."""
    destination = destination.absolute()
    if '..' in destination.parts:
        raise SystemExit('content archive output must use a canonical path')
    if destination.resolve().is_relative_to(ROOT.resolve()):
        raise SystemExit('content archive output must be outside the source repository')
    parent_fd = _output_parent(destination)
    try:
        parent = os.fstat(parent_fd)
        parent_identity = (parent.st_dev, parent.st_ino)
    finally:
        os.close(parent_fd)
    if not OUTPUT.is_file() or OUTPUT.read_bytes() != rendered.encode('utf-8'):
        raise SystemExit('release_snapshot_manifest.json is stale; regenerate before packaging')
    snapshot = standard_io.loads(rendered)
    expected = {row['path']: row['sha256'] for row in snapshot['artifacts']}
    expected[OUTPUT.name] = hashlib.sha256(rendered.encode('utf-8')).hexdigest()
    buffer = io.BytesIO()
    total = 0
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as zipped:
        for name, digest in sorted(expected.items()):
            path = ROOT / name
            if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
                raise SystemExit(f'content member is no longer a regular local file: {name}')
            with path.open('rb') as source:
                raw = source.read(4 * 1024 * 1024 + 1)
            total += len(raw)
            if len(raw) > 4 * 1024 * 1024 or total > 32 * 1024 * 1024:
                raise SystemExit('content exceeds the reference ZIP profile limits')
            if hashlib.sha256(raw).hexdigest() != digest:
                raise SystemExit(f'content changed during packaging: {name}')
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = (stat.S_IFREG | 0o644) << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            zipped.writestr(entry, raw)
    payload = buffer.getvalue()
    if len(payload) > 4 * 1024 * 1024:
        raise SystemExit('archive exceeds the reference ZIP profile limit')
    parent_fd = _output_parent(destination)
    try:
        parent = os.fstat(parent_fd)
        if (parent.st_dev, parent.st_ino) != parent_identity:
            raise SystemExit('content archive output parent changed during packaging')
        with os.fdopen(os.open(destination.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                               0o600, dir_fd=parent_fd), 'wb') as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)
    print(json.dumps(dict(archive=str(destination), sha256=hashlib.sha256(payload).hexdigest(),
        snapshotSha256=expected[OUTPUT.name], members=len(expected), qualificationEligible=False)))


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--archive", type=Path, help='create a checked flat content ZIP outside the source tree')
    args = parser.parse_args()
    rendered = json.dumps(build(), indent=2, ensure_ascii=False) + "\n"
    if args.archive is not None:
        archive(args.archive, rendered)
    elif args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != rendered:
            raise SystemExit("release_snapshot_manifest.json is stale")
    else:
        standard_io.write_text(OUTPUT, rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
