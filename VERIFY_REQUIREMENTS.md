# Verify Requirements — das-standard

```bash
./scripts/verify
```

## Prerequisites

- `python3` on PATH (3.10+)
- `bash` on PATH
- `jsonschema` installed from `requirements-verify.txt`

Install the pinned verification dependency set:

```bash
python3 -m pip install -r requirements-verify.txt
```

## What verify checks

1. VERSION file present and semver-valid.
2. CHANGELOG.md present.
3. standard_manifest.json present and schema-valid.
4. Release snapshot manifest present.
5. Compatibility alias resolution.
