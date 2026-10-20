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

## Choosing the minimum relevant check

| Invocation | Scope |
|---|---|
| `./scripts/verify` or `--gate all` | Common checks, all selected release-contract checks, residue check and pytest |
| `./scripts/verify --full` | Same default all-gates scope, labelled full mode |
| `./scripts/verify --gate schemas` | Common checks plus schema gate; no pytest suite |
| `./scripts/verify --full --gate schemas` | Still the selected schema gate; full mode does not expand gate selection |
| `./scripts/verify --gate compat-release` | Common checks and compatibility gate; skips generated-residue check |

Every selected gate still executes shared required-file, structure, manifest,
content/reference, index/module and snapshot-consistency checks. A gate is not
an isolated single-file validator. The shell entry records toolchain versions,
so even a gate that does not run pytest requires the pinned pytest package to be
installed. It clears `PYTEST_ADDOPTS` to prevent inherited selection narrowing.

Direct tools such as `python3 -B tools/validate_release_contract.py --gate schemas`
are narrower diagnostics, not substitutes for all shell-entry common checks.
Use the selected shell gate when checking the component contract; use focused
pytest node IDs for a behavior change. Reserve all/default runs for CI or a
specific broader risk, not every documentation edit.
