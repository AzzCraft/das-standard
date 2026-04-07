# Appendix L — DAS Tooling Standard (Reproducible Verify)

This appendix defines a **normative** tooling baseline to make `./scripts/verify` reproducible across:

- developer machines,
- CI runners,
- long-term maintenance windows (years).

> Rationale: If the toolchain drifts, “verify passed” becomes non-portable and non-auditable.

---

## L1. Containerized verify environment (preferred)

- **MUST:** `verify` MUST be runnable inside a container image pinned by **digest** (not a floating tag).
- **SHOULD:** Provide a developer-friendly entrypoint:
  - `./scripts/devshell` → opens a shell inside the pinned image
  - `./scripts/verify` → runs verify inside the pinned image by default

Example (informative):

```bash
# Pinned by digest (example)
IMAGE="ghcr.io/your-org/das-verify@sha256:..."
docker run --rm -t -v "$PWD:/work" -w /work "$IMAGE" ./scripts/verify --ci
```

---

## L2. Tooling.lock (required)

- **MUST:** The repo MUST define a lock mechanism that pins:
  - compilers/interpreters (version),
  - linters/formatters,
  - contract/code generators,
  - infrastructure tools used by gates (terraform, helm, etc.) if applicable.
- **MUST:** The lock MUST be referenced by CI, and **CI is the source of truth** for the gate toolchain.

Acceptable forms (choose one):

1. `tooling.lock` (YAML/JSON) listing tool names, versions, and optional SHA256.
2. `.tool-versions` (asdf) + container image digest.
3. A pinned CI image digest with an accompanying manifest.

---

## L3. No floating tool tags

- **MUST NOT:** Use `latest` for any tooling image used by `verify`.
- **MUST:** If an image is used, it MUST be pinned by digest; a semver tag MAY exist for readability but MUST NOT be the enforcement mechanism.

---

## L4. Verify report artifacts

- **SHOULD:** `verify` SHOULD output a structured report artifact, e.g.:

`artifacts/verify-report.json`

Minimum fields:

- `schemaVersion`
- `mode` (`fast|full|ci`)
- `repoSha`
- `toolchain` (image digest and/or tool versions)
- `gates[]` (name, status, duration, artifact links)
- `startTime`, `endTime`

---

## L5. Self-test for validation tools (regulated / high-stakes)

If a repository relies on a custom validation tool to gate releases (coverage parser, static analysis aggregator, contract diff tool):

- **SHOULD:** The tool MUST have a **self-test suite** that includes:
  - at least one **pass-case** input that should succeed,
  - at least one **fail-case** input that must fail.

`verify` SHOULD run tool self-tests before trusting tool outputs.

---

## L6. Mapping to profiles

Profiles may strengthen L1–L5:

- RTOS/Safety profiles often require compiler pinning + static analysis pinning (MISRA tool versions).
- Web3 requires pinned Solidity compiler + pinned chain fork configuration for deterministic gas/layout tests.
- DataOps requires pinned engine versions (Spark/Flink/dbt) and pinned schema registry client versions.
- GameDev requires pinned engine/toolchain versions and explicit asset build settings.

