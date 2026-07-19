# Appendix N - Repo Roles, Tooling Placement, and Execution Matrix

This appendix provides the canonical repo-role matrix for the DAS program and clarifies tool placement rules.

## Repo Roles

- `das-standard`: standard text and machine-readable canonical artifacts.
- `das-suite`: version closure and locked sync governance.
- `dasops`: product-repo seeding, adoption, and operator workflows.
- `cadence-oss`: open runtime/protocol/policy foundation.

## Tool Placement Rules

- Standard schemas and manifest contracts belong in `das-standard`.
- Cross-repo closure logic belongs in `das-suite`.
- Generic product-repo workflows belong in `dasops`.
- Product- or framework-specific specializations belong outside the generic OSS tools.
- Runtime protocol/schema execution belongs in `cadence-oss`.

## Execution Matrix

- PR blocking: schema integrity, closure integrity, and root verifier health.
- Merge-to-main: root + subunit verifiers for each touched repo.
- Nightly: expanded replay, migration, and compatibility checks.
- Pre-release: strict release-bundle and support-surface validation.
