# DAS v1.4.6 Release Notes

- **Version:** v1.4.6
- **Release date:** 2026-04-06
- **Positioning:** upgrades DAS from a document bundle into a **repo-canonical, self-verifying release artifact that can be locked, mirrored, and referenced by suites**.
- **Change type:** focused on repo-canonical release bundles, suite machine-readable locks, verify registry/report governance, and release snapshot governance.

## Highlights

1. **The standard repo now ships complete release and self-verification infrastructure**
   - Added `VERSION`.
   - Added root `scripts/verify`.
   - Added `.github/workflows/verify.yml`.
   - Added the committed `verify_registry.json`.
   - Added the committed `release_snapshot_manifest.json`.

2. **Suite locking now extends beyond version closure**
   - Added `suite_lock.schema.json` and `suite_lock.example.json`.
   - `suite_version_closure.schema.json` now requires `suiteLockRef`, linking closure and lock explicitly.

3. **Repo roles, tool placement, and execution lanes are now governed directly**
   - Added a repo-role taxonomy.
   - Added tool-class and placement-target taxonomies.
   - Added Appendix N to define repo roles, tool placement, and the execution matrix.

4. **Verify is now a machine-readable governance surface**
   - Added `verify_registry.schema.json` and its example.
   - Added `verify_report.schema.json` and its example.
   - The standard now defines formal semantics for `not_run`, `failureOnNoResults`, and per-gate cadence and enforcement.

5. **Release snapshots and local mirror provenance are now governed**
   - Added `release_snapshot_manifest.schema.json` and its example.
   - `tooling_lock.schema.json` now supports `standardSnapshotRef`, mirror provenance, and local-copy purpose.
   - Local standard copies and mirrors can no longer be treated as canonical truth without provenance.

6. **Master Doc readiness gates are easier to validate mechanically**
   - `standard_manifest.json` now includes `requiredSubsections`.
   - `master_doc` can now require `Document Control -> Doc readiness gate` in a machine-readable way.

7. **The extension mechanism now covers suite, tooling, and execution layers**
   - `local_extension_manifest.schema.json` can now extend `repoRoles`, `toolClasses`, `toolPlacementTargets`, `verifyGateKinds`, `moduleStates`, and `releaseSnapshotKinds`.

## Practical impact

- `das-standard` can now be referenced, validated, mirrored, and locked as a real standard release repository.
- `das-suite` can build clearer machine-readable governance around `suite.lock` and the module-state model.
- `dasops`, runtime repos, and product repos can build a more consistent execution and reporting surface around `verify_registry` and `verify_report`.
- Provenance management for local standard copies, template copies, and policy-pack copies is easier to machine-check.
