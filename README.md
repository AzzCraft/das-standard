# Docs as Software (DAS) Standard | 文码合一标准

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Standard Version](https://img.shields.io/badge/DAS-v1.4.6-blue)](SPECIFICATION.md)

Managed by **AzzCraft Inc.** (Chongqing AzzCraft Technology Co., Ltd.).

**Docs as Software (DAS)** is a pragmatic engineering standard for building software (especially AI-enabled products) with:
- a **real spec** (versioned, changelogged, conformance profiles),
- **contract-first boundaries** (schema + semantics + fixtures + executable checks), and
- **one-command verification** (`verify`) that keeps docs and code in lockstep.

This repository now publishes the **v1.4.6 repo-canonical release bundle** of the standard. `SPECIFICATION.md` remains the canonical entrypoint, the appendices are externalized under `appendices/`, and the governed machine-readable artifacts shipped with the release bundle live at the repo root.

## The Standard
The core technical specification and governing documents:
- **Spec:** [SPECIFICATION.md](SPECIFICATION.md)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Version marker:** [VERSION](VERSION)
- **Context Pack:** [DAS_STANDARD_CONTEXT_PACK.md](DAS_STANDARD_CONTEXT_PACK.md)
- **Deployment Addendum:** [DAS_DEPLOYMENT_ADDENDUM.md](DAS_DEPLOYMENT_ADDENDUM.md)
- **Governance & Collaboration Addendum:** [DAS_GOVERNANCE_COLLABORATION.md](DAS_GOVERNANCE_COLLABORATION.md)
- **Appendices:** [`appendices/`](appendices/)
- **Glossary:** [glossary.md](glossary.md)
- **Trademark policy:** [TRADEMARKS.md](TRADEMARKS.md)

## Machine-readable release artifacts
The v1.4.6 release bundle includes governed artifacts for tooling, suite closure, verification, release snapshots, and template discovery:
- **Standard manifest:** [standard_manifest.json](standard_manifest.json) + [standard_manifest.schema.json](standard_manifest.schema.json)
- **Suite closure + lock:** [suite_version_closure.schema.json](suite_version_closure.schema.json), [suite_version_closure.example.json](suite_version_closure.example.json), [suite_lock.schema.json](suite_lock.schema.json), [suite_lock.example.json](suite_lock.example.json)
- **Tooling + local extensions:** [tooling_lock.schema.json](tooling_lock.schema.json), [tooling_lock.example.json](tooling_lock.example.json), [local_extension_manifest.schema.json](local_extension_manifest.schema.json), [local_extension_manifest.example.json](local_extension_manifest.example.json)
- **Verify contracts:** [verify_registry.json](verify_registry.json), [verify_registry.schema.json](verify_registry.schema.json), [verify_report.schema.json](verify_report.schema.json), [verify_report.example.json](verify_report.example.json)
- **Release snapshots:** [release_snapshot_manifest.json](release_snapshot_manifest.json), [release_snapshot_manifest.schema.json](release_snapshot_manifest.schema.json), [release_snapshot_manifest.example.json](release_snapshot_manifest.example.json)
- **Template catalog:** [template_catalog.json](template_catalog.json) + [template_catalog.schema.json](template_catalog.schema.json)

Additional repo-support docs such as the community registry, glossary, trademark policy, contribution guide, and historical FAQ remain in this repository for reference. They are not part of the governed machine-readable release bundle unless explicitly listed in the release manifest.

## Compatibility aliases and consumer adoption

`standard_manifest.json` keeps two compatibility-friendly top-level arrays:

- `interactionProfiles`
- `gateCadences`

These alias the richer canonical definitions under:

- `enums.interactionProfiles`
- `enums.gateCadences`
- `gateCadenceDefinitions`

Consumers that only need a flat list can read the top-level aliases. Consumers that need the full governed shape, compatibility semantics, or cadence metadata should read the richer canonical structures instead.

Exact downstream guidance for the current foundation tranche lives in [CONSUMER_ADOPTION_NOTES.md](CONSUMER_ADOPTION_NOTES.md).

## Verification
This repo is self-checking. The canonical verification entrypoint is:

```bash
./scripts/verify
```

It validates the version marker, `standard_manifest.json`, and all shipped example/schema pairs used by the v1.4.6 release bundle. CI runs the same check via [`.github/workflows/verify.yml`](.github/workflows/verify.yml).

## Backward compatibility

`SPECIFICATION.md` keeps the appendix anchors, including the explicit Appendix D anchor, as stubs that link to the externalized appendix files. This preserves existing references such as `.../SPECIFICATION.md#appendix-d-ui-spec-appendix-template-v1` while allowing the appendix set to grow through Appendix N.

## Why DAS?
* **Consistency:** Treat docs like code (Linting, Testing, CI/CD).
* **Scalability:** A unified structure for enterprise knowledge bases and AI engineering.
* **Interoperability:** Build tools that work across any DAS-compliant project.

## Community & Registry
We are building a "Map of Open Source" by documenting popular repositories using the DAS Standard.

- [**View the Registry**](COMMUNITY_REGISTRY.md): See widely used projects (like React, Pandas, etc.) documented with DAS.
- **Submit a Doc:** Have you analyzed a public repo? [Submit your Master Doc](COMMUNITY_REGISTRY.md) to get featured as a contributor.

## Quick adoption path
DAS is designed to be readable by humans but **executable by AI agents**.

1. **Preparation:** Copy `SPECIFICATION.md` and your PRD doc to a new folder.
2. **Generate the master doc:** Ask an LLM to *"refer to SPECIFICATION.md and the PRD doc to generate the master_doc.md for this project"* or use `templates/prompts/generate_master_doc_from_PRD.md`.
3. **Verify conformance:** You may need to iterate a few times and ask the LLM to *"compare the master_doc.md against the SPECIFICATION.md and the PRD doc to check for errors"* or use `templates/prompts/verify_master_doc_against_PRD.md`.
4. **Generate the repo:** Ask the LLM to *"refer to SPECIFICATION.md and master_doc.md to implement the whole project"*.
5. **Add a feature:** Ask the LLM to *"refer to SPECIFICATION.md and master_doc.md to add a feature XXX"*.

## Versioning on GitHub

Use **Git tags / GitHub Releases** to version the entire document set as one unit:

- Tag the release commit as `v1.4.6`, `v1.4.5`, etc.
- Link to a stable version by pointing to the tag, e.g. `.../blob/v1.4.6/SPECIFICATION.md`.

## Licensing

- **Copyright:** © 2026 AzzCraft Inc. (Chongqing AzzCraft Technology Co., Ltd.)
- **License:** Specification & documentation are licensed under **CC BY 4.0** (see `LICENSE`).
  - *You are free to share and adapt this material as long as you provide attribution to AzzCraft Inc.*
- For copyright and other info, please **contact qipeng@azzcraft.com** or visit [**AzzCraft.com**](https://azzcraft.com).
