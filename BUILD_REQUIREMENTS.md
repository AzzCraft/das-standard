# Build Requirements — das-standard

das-standard has no application compilation step. It does generate derived
reading views/indexes and a deterministic content snapshot/ZIP for distribution.

## Toolchain

| Tool | Minimum | Purpose |
|------|---------|---------|
| `bash` | 3.2+ | verify script |
| `python3` | 3.10+ | schema validation in verify |
| `git` | 2.30+ | version pinning |

Install pinned verification dependencies before running local, CI, or release
verification:

```bash
python3 -m pip install -r requirements-verify.txt
```

`requirements-verify.txt` pins `jsonschema` for schema validation and
`pytest` for the repository's self-conformance tests. Both are required by
`scripts/verify`.

## Content generation and packaging

From this repository root, after the author/index updates described in
[GOVERNANCE.md](GOVERNANCE.md):

```bash
python3 -B tools/generate_content_snapshot.py --check
```

This checks the committed `release_snapshot_manifest.json` against current
content. After an intentional content change, run the same command without
arguments to regenerate that manifest, then inspect its diff and run `--check`.
Neither command creates a ZIP by default.

To package current content, set `CONTENT_ZIP` to a new filename in an existing
output directory **outside this source repository**:

```bash
python3 -B tools/generate_content_snapshot.py --archive "$CONTENT_ZIP"
```

Use a normalized path with no `..` components and no symlinked parent. The output
file must not exist. A stale snapshot refuses packaging; regenerate and review
it first. The generator includes only the declared content profile and its
snapshot, verifies member bytes and writes a deterministic ZIP. It is different
from a Git source archive containing the full tool/tests/workflows.

The JSON receipt reports `archive`, `sha256`, `snapshotSha256`, `members` and
`qualificationEligible=false`. These are content identities, not execution of
all acceptance cases or release approval. Source publication and release
validation remain the separate steps in GOVERNANCE.md.
