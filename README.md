# DAS Standard

The **Docs as Software (DAS) Standard** (中文：**文码合一标准**) is a normative
engineering specification for maintaining documentation, contracts, and
verification as versioned software artifacts.

This repository is the canonical source of:

- The normative specification (`SPECIFICATION.md`) and complete machine indexes (`chapter_index.json`,
  `clause_index.json`).
- Conformance profiles and machine-readable schemas referenced by DAS tooling.
- Governance and adoption guidance (`DAS_GOVERNANCE_COLLABORATION.md`,
  `CONSUMER_ADOPTION_NOTES.md`, `COMMUNITY_REGISTRY.md`).
- Normative appendices and adoption guidance.

## Companion repos

| Repo                | Role                                                             |
| ------------------- | ---------------------------------------------------------------- |
| `das-suite`         | Workspace and version-closure CLI.                               |
| `dasops`            | Change-container operations.                                     |
| `cadence-oss`       | Open-source verification engine.                                 |

## Versioning

This repo follows semantic versioning. The current version is in
[`VERSION`](VERSION). Breaking changes to clause IDs require a major bump.
The checked-in release snapshot is a reproducible content manifest, not a Git
commit attestation; final commit and artifact binding is produced externally by
the release pipeline.

## Citation

See [`citation.cff`](citation.cff) for academic citation metadata.

## License

See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Code of conduct,
governance, and review process are documented in
[`DAS_GOVERNANCE_COLLABORATION.md`](DAS_GOVERNANCE_COLLABORATION.md).
