# Verify Requirements — das-standard

```bash
bash scripts/verify
```

## Prerequisites

- `python3` on PATH (3.10+)
- `bash` on PATH

## What verify checks

1. VERSION file present and semver-valid.
2. CHANGELOG.md present.
3. standard_manifest.json present and schema-valid.
4. Release snapshot manifest present.
5. Compatibility alias resolution.
