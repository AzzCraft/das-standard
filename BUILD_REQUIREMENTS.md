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

Invoke maintenance helpers with `python3 -I -B` or the shipped shell wrapper,
using an interpreter with these dependencies installed. Helpers also restart
with isolation before loading their verification dependencies. This restart
cannot undo startup code already run by an initial interpreter without `-I`. `PYTHONPATH` and user-site
packages do not supply their verification dependencies. JSON maintenance
inputs reject duplicate keys, non-JSON constants and decimal overflow or
nonzero underflow outside binary64 range, and value-changing decimal round-trips;
ordinary representable decimal spellings use binary64,
while integer tokens retain Python integer precision. This is not a change to
the separately specified exact-number exchange contracts.

Applicability facts describe distinct events: `activity.standard_release` is
publishing the Standard, `activity.product_adoption` is a product's adoption,
`activity.package_activation` is activating an adopted package, and
`activity.continued_operation` is operating under it. A new protected action
uses `activity.protected_action`. Publishing false cannot waive product duties;
missing/conflicting facts retain the preview's unknown/conflict behavior.

## Content generation and packaging

From this repository root, after the author/index updates described in
[GOVERNANCE.md](GOVERNANCE.md):

```bash
python3 -I -B tools/generate_content_snapshot.py --check
```

This checks the committed `release_snapshot_manifest.json` against current
content. After an intentional content change, run the same command without
arguments to regenerate that manifest, then inspect its diff and run `--check`.
Neither command creates a ZIP by default.

To package current content, set `CONTENT_ZIP` to a new filename in an existing
output directory **outside this source repository**:

```bash
python3 -I -B tools/generate_content_snapshot.py --archive "$CONTENT_ZIP"
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
