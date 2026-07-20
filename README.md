# DAS Standard

The **Docs as Software (DAS) Standard** (中文：**文码合一标准**) is a normative engineering specification for maintaining documentation, contracts, and verification as versioned software artifacts.

This repository is self-contained: it can be read, adopted, validated, cited, and released without any companion repository. Its canonical public materials are:

- The normative specification ([SPECIFICATION.md](SPECIFICATION.md)) and complete machine indexes ([chapter_index.json](chapter_index.json), [clause_index.json](clause_index.json)).
- Machine-readable schemas, the [standard manifest](standard_manifest.json), stable IDs, templates, and governed appendices.
- Governance, adoption, registry, verification, and reproducible release-snapshot materials.

## Quick start

~~~bash
python3 -m pip install -r requirements-verify.txt
./scripts/verify
~~~

Read [SPECIFICATION.md](SPECIFICATION.md) to adopt the standard, then use the templates in [Appendix M](appendices/appendix-m-doc-family-governance-and-module-doc-templates.md).

## Optional ecosystem integrations

The DAS Standard does not depend on a specific tool or repository. Implementations may optionally integrate with independently released tooling, such as a suite-level version-closure tool, a repository-adoption tool, or a verification runtime. Such integrations are non-normative and must not change this repository's standalone conformance requirements.

## Versioning

This repo follows semantic versioning. The current version is in [VERSION](VERSION). Breaking changes to clause IDs require a major bump. The checked-in release snapshot is a reproducible content manifest, not a Git commit attestation; final commit and artifact binding is produced externally by the release pipeline.

## Citation

See [citation.cff](citation.cff) for academic citation metadata.

## License

See [LICENSE](LICENSE) and [NOTICE](NOTICE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [DAS_GOVERNANCE_COLLABORATION.md](DAS_GOVERNANCE_COLLABORATION.md) for governance and review expectations.
