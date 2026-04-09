# VERSION NOTES – DAS v1.4.4

> **Status**: Frozen  
> **Governing standard**: DAS v1.4.6  
> **Released**: 2025-Q4

## Summary

DAS v1.4.4 introduced:

- Machine-readable `standard_manifest.json` and its companion schema.
- `suite_version_closure.schema.json` for multi-repo version closure.
- `tooling_lock.schema.json` for governed tooling references.
- `local_extension_manifest.schema.json` for product-local extensions.
- Appendix L (tooling standard) and Appendix M (doc family governance).

## Breaking Changes from v1.4.3

| Area | Change |
|------|--------|
| Manifest | `standard_manifest.json` now required at repo root |
| Closure | `suite_version_closure.schema.json` replaces ad-hoc lock files |
| Tooling | `tooling_lock.json` becomes source of truth for tool versions |

## Upgrade Path

Repos adopting v1.4.4+ from earlier versions should:

1. Run `dasops adopt` to generate missing artifacts.
2. Validate with `scripts/verify` — all new schema gates are blocking at `pr_blocking` cadence.
3. Review and resolve any `local_extension_manifest.json` declarations against the new schema.

## Superseded By

DAS v1.4.6 — current governing version. See CHANGELOG.md for incremental changes.
