# DAS Standard

The **Docs as Software (DAS) Standard** (中文：**文码合一标准**) is a normative engineering specification for maintaining documentation, contracts, and verification as versioned software artifacts.

This repository is self-contained: it can be read, adopted, validated, cited, and released without any companion repository. Its canonical public materials are:

- The normative specification ([SPECIFICATION.md](SPECIFICATION.md)) and complete machine indexes ([chapter_index.json](chapter_index.json), [clause_index.json](clause_index.json)).
- Machine-readable schemas, the [standard manifest](standard_manifest.json), stable IDs, templates, and governed appendices.
- Governance, adoption, registry, verification, and reproducible release-snapshot materials.

The current source edition is **1.5.0-beta.1, an unpublished content candidate**.
The [normative additions](modules/edition-1.5.md) author the new semantics;
Chapter 13 of the specification is their generated view. The
[acceptance obligations](modules/acceptance-1.5.md) preserve all 136 product cases.
Content checks do not qualify beta, activate protected actions or prove that
these cases ran. The complete 3.0.0 leaf catalog maps 1,745 legacy and 978 edition
obligations; mapping completion does not certify tool implementation or deployment.
Versioned reference contracts and consumers are available. Complete tool scenarios,
installed reference deployment, final compatibility approval and publication
remain unfinished. Historical 1.4 artifacts retain their original meaning.

The [reference exchange schemas](contracts/das_v1_5/README.md) are shipped as
controlled protocol copies with the manifest and snapshot. They can be inspected
and checked offline in this repository. They describe implemented reference
exchanges and do not qualify the unfinished formal product chain.

## Quick start

~~~bash
python3 -m pip install -r requirements-verify.txt
./scripts/verify
~~~

Read [SPECIFICATION.md](SPECIFICATION.md) to adopt the standard, then use the templates in [Appendix M](appendices/appendix-m-doc-family-governance-and-module-doc-templates.md).

To produce the flat content ZIP consumed by reference tooling, first verify this
edition, then run from this repository:

~~~bash
python3 -B tools/generate_content_snapshot.py --archive /absolute/output/standard-content.zip
~~~

The output directory must exist outside this repository; existing files are never
overwritten. This packages exactly the checked snapshot members and the snapshot
itself, with stable ZIP metadata. It refuses stale content. The ZIP, raw snapshot
and source archive have separate byte digests. A source archive also contains the
tests and verification tools needed for independent validation; the content ZIP
is the runtime reading payload. Packaging establishes neither approval nor release.

## Optional ecosystem integrations

The DAS Standard does not depend on a specific tool or repository. Implementations may optionally integrate with independently released tooling, such as a suite-level version-closure tool, a repository-adoption tool, or a verification runtime. Such integrations are non-normative and must not change this repository's standalone conformance requirements.

Official companion readiness requires the joint gates in Chapter 13, including
minimal HTTP, UI and sealed-evaluation samples. Other implementations may provide
equivalent evidence. A project proves applicability from its actual capabilities;
it does not have to deploy a named product to implement the standard.

## Versioning

This repo follows semantic versioning. The current source version is in [VERSION](VERSION).
The final compatibility decision must assess public contracts and MUST obligations,
including migration; unchanged clause IDs alone do not prove a compatible minor.
The checked-in release snapshot is a reproducible content manifest, not a Git
commit attestation or publication receipt. Its declared date is a content edition
date. Final source/artifact binding and actual publication events are recorded
outside the immutable payload by the protected release pipeline.

## Citation

See [citation.cff](citation.cff) for academic citation metadata.

## License

See [LICENSE](LICENSE) and [NOTICE](NOTICE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [DAS_GOVERNANCE_COLLABORATION.md](DAS_GOVERNANCE_COLLABORATION.md) for governance and review expectations.

## Legacy baseline provenance and public verification

`migration/legacy_normative_baseline.json` retains its captured source claim
`6d90333aea16987fc490570746fb5f93c930b970`. That object is not available from
this public repository. This does not establish the history of that capture.
The 17 recorded source files are content-equivalent to public v1.4.0 commit
`ac5a52fe9e8997392b3d21a488097e394d8e3102`. The baseline bytes and independent
SHA-256 pin `d0c337fd2dc69b9343b6ddc500b0c4209947dca5288f3b6a017662abc7081caf`
remain unchanged. Content equivalence is not a claim that the commits share provenance.

From this checkout, with the public v1.4.0 object available, verify the equivalence:

```bash
python3 - <<'PYCODE'
import hashlib, json, subprocess
from pathlib import Path
commit = "ac5a52fe9e8997392b3d21a488097e394d8e3102"
for item in json.loads(Path("migration/legacy_normative_baseline.json").read_text())["sources"]:
    raw = subprocess.check_output(["git", "show", commit + ":" + item["path"]])
    if hashlib.sha256(raw).hexdigest() != item["sha256"]:
        raise SystemExit("Content differs: " + item["path"])
print("Public content equivalence verified: 17 files")
PYCODE
```

Missing Git objects are an unavailable provenance check, not a content PASS.
Normal offline content verification needs no Git-history retrieval.
