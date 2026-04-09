# DAS Standard Consumer Adoption Notes

This note records how downstream repos should consume the governed `das-standard` v1.4.6 release bundle without rewriting the public contract.

## Canonical vs compatibility fields

`standard_manifest.json` keeps two compatibility-friendly top-level arrays:

- `interactionProfiles`
- `gateCadences`

These are aliases for the canonical richer structures:

- `enums.interactionProfiles`
- `enums.gateCadences`
- `gateCadenceDefinitions`

Use the top-level aliases only when a consumer needs a flat compatibility list. Use the canonical structures when a consumer needs metadata, compatibility windows, or cadence semantics.

## Downstream consumers in the current program

- `das-suite`
  - Consumes the governed bundle as the suite-wide standard reference.
  - Uses the flat aliases for compatibility checks and the richer definitions for upgrade/report surfaces.
- `dasops`
  - Seeds product repos with governed references and machine-readable lock/config examples from the release bundle.
  - Must not copy standard prose into generated repos.
- `das-leafer`
  - Consumes the same governed standard artifacts indirectly through `dasops` plus Leafer-owned HFVI overlays.
  - Must not fork generic standard handling locally.
- `cadence-core`
  - Uses the v1.4.6 profile/cadence family as the policy/runtime alignment target.
  - Should read canonical cadence/profile definitions when enforcing runtime behavior.

## Adoption rules

- Do not change the public manifest shape from `v1.4.6`.
- Do not remove `interactionProfiles` or `gateCadences`; they remain required compatibility aliases.
- Do not treat `gateCadenceDefinitions` as redundant. It is the canonical richer cadence surface.
- Prefer explicit versioned references to the release bundle rather than copying artifacts ad hoc.
