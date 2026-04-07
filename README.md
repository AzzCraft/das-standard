# Docs as Software (DAS) Standard | 文码合一标准

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Standard Version](https://img.shields.io/badge/DAS-v1.3.0-blue)](SPECIFICATION.md)

Managed by **AzzCraft Inc.** (Chongqing AzzCraft Technology Co., Ltd.).

**Docs as Software (DAS)** is a pragmatic engineering standard for building software (especially AI-enabled products) with:
- a **real spec** (versioned, changelogged, conformance profiles),
- **contract-first boundaries** (schema + semantics + fixtures + executable checks), and
- **one-command verification** (`verify`) that keeps docs and code in lockstep.

This repository now publishes the **v1.3.0 modular distribution** of the standard while preserving the supporting materials that were already present in the v1.1.0 repository. `SPECIFICATION.md` remains the canonical entrypoint, and large appendices are externalized under `appendices/`.

## The Standard
The core technical specification and governing documents:
- **Spec:** [SPECIFICATION.md](SPECIFICATION.md)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Context Pack:** [DAS_STANDARD_CONTEXT_PACK.md](DAS_STANDARD_CONTEXT_PACK.md)
- **Deployment Addendum:** [DAS_DEPLOYMENT_ADDENDUM.md](DAS_DEPLOYMENT_ADDENDUM.md)
- **Governance & Collaboration Addendum:** [DAS_GOVERNANCE_COLLABORATION.md](DAS_GOVERNANCE_COLLABORATION.md)
- **Appendices:** [`appendices/`](appendices/)
- **Glossary:** [glossary.md](glossary.md)
- **Trademark policy:** [TRADEMARKS.md](TRADEMARKS.md)

## Backward compatibility

`SPECIFICATION.md` keeps the original Appendix C-K headings, including the explicit Appendix D anchor, as stubs that link to the externalized appendix files. This preserves existing references such as `.../SPECIFICATION.md#appendix-d-ui-spec-appendix-template-v1`.

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

- Tag the release commit as `v1.3.0`, `v1.2.1`, etc.
- Link to a stable version by pointing to the tag, e.g. `.../blob/v1.3.0/SPECIFICATION.md`.

## Licensing

- **Copyright:** © 2026 AzzCraft Inc. (重庆艾之舟科技有限公司)
- **License:** Specification & documentation are licensed under **CC BY 4.0** (see `LICENSE`).
  - *You are free to share and adapt this material as long as you provide attribution to AzzCraft Inc.*
- For copyright and other info, please **contact qipeng@azzcraft.com** or visit [**AzzCraft.com**](https://azzcraft.com).
