# Appendix N - Repository Roles, Tooling Placement, and Execution Matrix

This appendix defines generic roles that a DAS adoption may assign to one or more repositories. The roles describe responsibility boundaries, not required repository names or dependencies.

## Repository roles

- **standard_repo:** owns the normative standard text, machine-readable schema, templates, and versioned release artifacts.
- **suite_repo:** owns locked version closure and coordinated multi-repository verification.
- **factory_repo:** owns repeatable scaffolding, adoption, or migration workflows for product repositories.
- **verify_runtime_repo:** owns reusable verification runtime, protocol, or policy execution components.
- **policy_pack_repo:** owns reusable policy, checks, or configuration packs.
- **product_repo:** owns a product's implementation and its local conformance evidence.
- **monorepo_local_tooling:** owns tooling intentionally scoped to one monorepo.

A single repository MAY serve more than one role, and an adoption MAY use only the roles it needs.

## Tool placement rules

- Put normative schemas, stable IDs, and template contracts in the **standard_repo**.
- Put multi-repository locks and version-closure orchestration in a **suite_repo**.
- Put reusable seeding and adoption workflows in a **factory_repo**.
- Put reusable protocol or verification execution in a **verify_runtime_repo**.
- Keep product-specific implementation and local specializations in the **product_repo** or **monorepo_local_tooling** boundary.
- Do not make a tool a dependency of the standard merely because it implements or consumes part of the standard.

## Execution matrix

- **PR blocking:** schema integrity, required document metadata, links, and root verifier health.
- **Merge-to-main:** root verification plus relevant subunit verification for each touched component.
- **Nightly:** expanded replay, migration, compatibility, and audit checks.
- **Pre-release:** strict release-bundle, snapshot, legal, security, and support-surface validation.
