# Verify Requirements — das-standard

```bash
./scripts/verify
```

## Prerequisites

- `python3` on PATH (3.10+)
- `bash` on PATH
- `jsonschema` and `pytest` installed from `requirements-verify.txt`

Install the pinned verification dependency set:

```bash
python3 -m pip install -r requirements-verify.txt
```

## What verify checks

1. Required artifacts, governed references, VERSION alignment, and Markdown links.
2. Manifest, registry, report, snapshot, index, and stable-ID schema validation.
3. Appendix M templates and normative-addendum metadata/section conformance.
4. Enum-definition parity, stable appendix IDs, and context-pack references.
5. Snapshot hashes, registry-to-verifier gate parity, compatibility fixtures, and generated-output freshness.
6. Generated-residue checks and the repository self-conformance test suite.

Use `./scripts/verify --full` to label an explicit full run. It executes the same governed release checks as the default all-gates command; use `./scripts/verify --gate <name>` for one registry-backed gate.
