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
- AzzCraft Inc. (重庆艾之舟科技有限公司)

## Versioning

The DAS Standard uses **Semantic Versioning (SemVer)**: `MAJOR.MINOR.PATCH`.

- **PATCH**: clarifications, typos, reformatting, or non-semantic edits that do not change any MUST/SHOULD semantics.
- **MINOR**: backward-compatible additions (new recommended practices, new optional sections, new conformance checks that can be ignored by older adopters).
- **MAJOR**: breaking changes to requirements, conformance rules, or compatibility windows.

A release is identified by an annotated `v<SemVer>` tag, including prereleases such as `v1.5.0-beta.1`.

## Release process

1. Merge the intended source changes through the repository's PR/CI rules.
   Update `CHANGELOG.md`, `VERSION` and matching manifest/metadata; prepare the
   checked content snapshot and review the public source contents.
2. A maintainer creates an **annotated** `v<SemVer>` tag whose suffix exactly
   matches `VERSION`. The target commit must be reachable from the repository's
   default branch; it need not equal the current tip. Lightweight tags reject.
3. Run the `release-validation` workflow from the default branch with its `ref`
   input set to that exact tag. See [release.yml](.github/workflows/release.yml).
   It binds the tag object, target commit, VERSION and default-branch ancestry,
   verifies source/tooling and builds the source/evidence artifacts.
4. The trusted stage independently rebuilds the evidence and attests the exact
   `das-standard-<version>-evidence.tar`. That direct attestation subject contains
   the source archive, SBOM, content ZIP/snapshot where applicable, manifest and
   checksums; it does **not** directly attest each inner file as a separate subject.
   The trusted job also retains this exact tar in the Actions artifact
   `das-standard-attested-evidence-<run_id>-<run_attempt>` for 30 days. Download
   that artifact, extract the outer ZIP, and verify the tar before using its
   contents: `gh attestation verify das-standard-<version>-evidence.tar --repo AzzCraft/das-standard`.
   Compare the verified source/workflow identity to the reviewed run; retain the
   tar, SHA-256 and verification output before expiry. The ZIP and inner source
   archive are different byte objects, so neither substitutes for the subject.
5. Review the validation output and its identities before publishing. This
   workflow does not create a tag or GitHub Release. The maintainer performs the
   separately authorized publication and checks the published bytes against the
   validated evidence. Validation success alone is not publication.

See [the Standard](SPECIFICATION.md), §13.21, for the source publication and
qualification boundary. Reading, citing, validating or packaging the Standard
is independent of running an adopter production environment.

## Change process

1. **Discuss first**: open a GitHub Issue describing the motivation, scope, and expected impact.
2. **Propose**: for non-trivial changes, add a proposal document under `proposals/` (a “DAS Improvement Proposal”, DIP).
3. **Implement**: submit a Pull Request updating:
   - the authored chapter source (`modules/` for 1.5; see below)

4. **Review**: maintainers review for correctness, backwards compatibility, and clarity.
5. **Merge**: once approved, the PR is merged to `main`.
6. **Release**: maintainers cut a tagged release when the change is ready for adoption.

## Canonical spec and forks

Forks are welcome. However:
- The **canonical specification** is the one published in this repository.

If you publish a forked variant, please use a different name to avoid confusing users.

## Editing Standard 1.5

Edit `modules/edition-1.5.md` and `modules/acceptance-1.5.md` for 1.5 prose.
Chapter 13 in `SPECIFICATION.md` is a generated reading view, not a second author.
Legacy chapters remain authored in `SPECIFICATION.md` and their named appendices.
Run `python3 -I -B tools/validate_modules.py`, then
`python3 -I -B tools/generate_spec_indexes.py` when headings/indexes change, update
affected artifact digests in `release/release_report.json`, and finally run
`python3 -I -B tools/generate_content_snapshot.py`.
Use the affected `scripts/verify --gate <name>` checks while developing; they
also enforce common index/module/snapshot consistency. Default/all runs the broader tests; `--full` labels the run mode and does not
override an explicitly selected gate. Content validation, ZIP generation, release-validation
and publishing are distinct operations. A checked-in snapshot is an input
identity record, not a new execution report for each invocation; registry
`producesArtifacts`/`expectedArtifactCount` describe that declared artifact
contract and do not prove a file was freshly produced.
`diff_standard old [new] [--stat]` compares only `SPECIFICATION.md` and appendices.
