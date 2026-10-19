# Contributing

Thanks for taking the time to improve the DAS Standard.

Because this repository contains a **formal specification**, we try to keep changes deliberate, reviewable, and easy to adopt.

## How to propose changes

1. **Open an Issue first**
   - describe the problem,
   - describe the proposed change,
   - describe compatibility impact and who will be affected.
2. **Submit a Pull Request**
   - update the authored chapter source (`modules/` for 1.5; see below) and affected templates/examples,
   - update `CHANGELOG.md` for user-visible semantic changes,
   - keep examples minimal and non-proprietary.

## Style guidelines

- Prefer the BCP 14 keywords: MUST, MUST NOT, SHOULD, SHOULD NOT, MAY.
- When adding a new requirement, include motivation and a minimal example.
- Avoid company-specific tooling or dependencies unless clearly labeled as non-normative.

## Licensing of contributions

By contributing to this repository, you agree that your contributions are licensed under the repository’s licensing scheme:
- **Specification & documentation** contributions are under **CC BY 4.0** (see `LICENSE`).
- **Scripts, schemas, examples, templates, tests, indexes, and machine-readable metadata** contributions are under **Apache-2.0** (see `LICENSE_MAP.md`).

## Developer Certificate of Origin

We recommend using a DCO-style sign-off on commits:

```text
Signed-off-by: Your Name <your.email@example.com>
```

This indicates you have the right to submit the work under the project licenses.

## Editing Standard 1.5

Edit `modules/edition-1.5.md` and `modules/acceptance-1.5.md` for 1.5 prose.
Chapter 13 in `SPECIFICATION.md` is a generated reading view, not a second author.
Legacy chapters remain authored in `SPECIFICATION.md` and their named appendices.
Run `python3 -B tools/validate_modules.py`, then
`python3 -B tools/generate_spec_indexes.py` when headings/indexes change, update
affected artifact digests in `release/release_report.json`, and finally run
`python3 -B tools/generate_content_snapshot.py`.
Use the affected `scripts/verify --gate <name>` checks while developing; they
also enforce common index/module/snapshot consistency. Default/all/`--full`
runs the broader tests. Content validation, ZIP generation, release-validation
and publishing are distinct operations. A checked-in snapshot is an input
identity record, not a new execution report for each invocation; registry
`producesArtifacts`/`expectedArtifactCount` describe that declared artifact
contract and do not prove a file was freshly produced.
`diff_standard old [new] [--stat]` compares only `SPECIFICATION.md` and appendices.
