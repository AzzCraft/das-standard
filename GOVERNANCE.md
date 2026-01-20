# Governance

This repository is the canonical home of the **DAS: Docs as Software Standard**.

The goal of governance is to keep the standard:
- stable enough for wide adoption,
- evolvable without breaking downstream users, and
- anchored by a clear, public change process.

## Roles

### Maintainers (Editors)
Maintainers are responsible for:
- reviewing and merging changes to the spec,
- publishing releases and changelog entries,
- acting as the final arbiter when there is disagreement.

Initial maintainer(s):
- AzzCraft Technology Team

## Versioning

The DAS Standard uses **Semantic Versioning (SemVer)**: `MAJOR.MINOR.PATCH`.

- **PATCH**: clarifications, typos, reformatting, or non-semantic edits that do not change any MUST/SHOULD semantics.
- **MINOR**: backward-compatible additions (new recommended practices, new optional sections, new conformance checks that can be ignored by older adopters).
- **MAJOR**: breaking changes to requirements, conformance rules, or compatibility windows.

A release is identified by a Git tag `vX.Y.Z`.

## Release process

A release MUST include:
- an updated `CHANGELOG.md` entry,
- updated version badges/metadata where relevant,
- a Git tag `vX.Y.Z` created from `main`.

## Change process

1. **Discuss first**: open a GitHub Issue describing the motivation, scope, and expected impact.
2. **Propose**: for non-trivial changes, add a proposal document under `proposals/` (a “DAS Improvement Proposal”, DIP).
3. **Implement**: submit a Pull Request updating:
   - `SPECIFICATION.md`

4. **Review**: maintainers review for correctness, backwards compatibility, and clarity.
5. **Merge**: once approved, the PR is merged to `main`.
6. **Release**: maintainers cut a tagged release when the change is ready for adoption.

## Canonical spec and forks

Forks are welcome. However:
- The **canonical specification** is the one published in this repository.

If you publish a forked variant, please use a different name to avoid confusing users.
