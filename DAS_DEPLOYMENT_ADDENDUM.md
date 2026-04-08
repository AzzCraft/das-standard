# DAS Deployment & Environment Addendum (DAS-Deploy)

## Document Control
- Doc ID: DAS-ADDENDUM-DEPLOYMENT
- Owner: DAS Maintainers
- Status: active
- Governing standard: SPECIFICATION.md
- Last updated: 2026-04-06
- Scope: Deployment, environment strategy, release artifact identity, supply-chain controls, migrations, and rollback guidance shipped with the DAS v1.4.6 release.
- Parent standard: SPECIFICATION.md
- Doc family role: subordinate_doc
- Addendum kind: deployment

## Normative language

This document uses BCP 14 requirement keywords (**MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**) as defined in the main DAS Standard.

---

## 1. Purpose and scope

The main DAS Standard focuses on **design + implementation + verification**. This addendum extends DAS to cover:

- environment strategy (`local`, `dev`, `staging`, `prod`, plus canary/shadow/perf),
- CI/CD pipelines and artifact promotion,
- secrets/config governance,
- infrastructure-as-code (IaC) and cloud resources,
- external vendors and AI service providers,
- production readiness (observability, incident response, rollback).

This is required for most real-world L1/L2 products. Pure libraries or research-only repos MAY adopt a reduced subset.

---

## 2. Definitions

- **Environment**: a deployed context with distinct configuration, data constraints, and access controls (e.g., `dev`, `staging`, `prod`).
- **Promotion**: moving *the same* build artifact (image/package) between environments with configuration changes only.
- **Release artifact**: a build output that is immutable and addressable (container digest, signed bundle, versioned package).
- **IaC**: declarative definition of infrastructure (Terraform, Pulumi, CloudFormation, Helm, etc.) committed to version control.
- **Dependency Registry**: a documented inventory of external dependencies (cloud services, vendors, AI providers) with owners and contracts.
- **Runbook**: an operational procedure for common actions (deploy, rollback, scale, rotate keys, mitigate incidents).

---

## 3. Environment model and data discipline

### 3.1 Required baseline environments

Projects SHOULD standardize at least:

- `local`: developer laptop + local containers
- `ci`: ephemeral test env (in CI)
- `dev`: integration testing for feature work
- `staging`: release-candidate validation
- `prod`: production

Projects MAY additionally define:

- `preview`: per-PR environments
- `canary`: limited traffic prod deployment
- `shadow`: prod traffic mirrored to a new version (no user impact)
- `perf`: load/performance testing

### 3.2 Environment Matrix (required for L1/L2)

**MUST (L1/L2):** Each project MUST maintain an **Environment Matrix** (as part of the Master Doc set) with, at minimum:

| Environment | Purpose | Data class allowed | Secrets strategy | External deps mode | Deploy method | Rollback | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- |

Rules:

- **MUST:** Each environment MUST declare which **data classification** is allowed (e.g., synthetic only; masked; production PII).
- **MUST:** Production data MUST NOT be used in non-prod environments by default.
- **MUST:** If production-like data is required in non-prod, the project MUST document masking/anonymization and approval controls.
- **MUST:** Environment-specific endpoints and credentials MUST be treated as secrets/config (see §5).

### 3.3 Environment parity and drift

- **SHOULD:** `staging` SHOULD be production-like in topology and dependencies, except for data.
- **MUST (L2):** L2 projects MUST define which differences between `staging` and `prod` are allowed, and why.
- **SHOULD:** Projects SHOULD run “drift checks” for IaC (declared vs actual) on a schedule.

---

## 4. Build artifacts, immutability, and promotion

### 4.1 Artifact immutability

- **MUST:** Release artifacts MUST be immutable and uniquely addressable.
  - Containers SHOULD be pinned by **digest** (not only `:tag`).
  - Packages MUST have a version (and ideally a cryptographic signature).
- **MUST:** A deployment MUST record the exact artifact identity (digest/version) and config identity (see §5) used.

### 4.2 Promotion strategy

- **SHOULD:** Prefer **promote-the-same-artifact** across envs (`dev` → `staging` → `prod`).
- **MAY:** Rebuild-per-env MAY be used if required by policy, but then:
  - **MUST:** builds MUST be reproducible,
  - **MUST:** build inputs MUST be pinned,
  - **MUST:** the pipeline MUST provide provenance.

### 4.3 Release notes and rollback correctness

- **MUST:** Each release MUST produce release notes including: schema/contract changes, migrations, and rollback constraints.
- **MUST:** If rollback is unsafe (irreversible migrations), the release MUST document a rollback alternative (forward-fix, feature flag disable, etc.).

---

## 5. Configuration and secrets governance

### 5.1 Configuration identity

- **MUST:** Config MUST be versioned and referenced by an identifier (e.g., `configId`, `profileId`).
- **MUST:** Config changes MUST be reviewed like code (PR + approvals).
- **SHOULD:** Config SHOULD be schema-validated.

### 5.2 Secrets

- **MUST:** Secrets MUST NOT be stored in git.
- **MUST:** Secrets MUST be managed by an approved secret manager (cloud secret manager, Vault, etc.).
- **MUST:** Secret rotation procedures MUST exist (runbooks).
- **SHOULD:** Use separate credentials per environment.

### 5.3 Feature flags

- **SHOULD:** Behavioral changes SHOULD be guarded by feature flags when:
  - the change is high risk,
  - rollback is hard,
  - or partial rollout is desired.
- **MUST (L2):** L2 programs MUST define a feature-flag lifecycle (create → rollout → remove).

---

## 6. Infrastructure as Code (IaC) and cloud resources

### 6.1 IaC as the source of truth

- **MUST (L1/L2):** Cloud resources used by production systems MUST be defined in IaC.
- **MUST:** IaC MUST be version-controlled and reviewed via PRs.
- **SHOULD:** Enforce least privilege for cloud IAM.

### 6.2 Resource inventory

**MUST (L1/L2):** The Master Doc set MUST include a pointer to a resource inventory describing:

- compute (k8s, serverless, VM),
- data stores,
- message/stream systems,
- observability stack,
- secrets manager,
- network controls (VPC, firewall, egress rules).

### 6.3 Supply chain controls (recommended; required for L2)

Modern incidents frequently originate in third-party and transitive dependencies. Supply chain controls make “what is running” auditable.

#### 6.3.1 Dependency pinning (required)

- **MUST:** Repos MUST use lockfiles / checksums for dependencies (language-appropriate), and CI MUST build in “frozen lockfile” mode.
  - Examples: `npm ci`, `pip --require-hashes`, `go mod verify`, `cargo --locked`.
- **MUST:** Build pipelines MUST fail if dependency resolution would change the lock state.

#### 6.3.2 SBOM generation (required for L2; recommended otherwise)

- **MUST (L2):** Every production artifact MUST produce an SBOM (SPDX or CycloneDX).
- **SHOULD:** SBOMs SHOULD be stored alongside build artifacts and referenced in Release Notes / manifests.

#### 6.3.3 Vulnerability policy and scanning (required for L2)

- **MUST (L2):** CI MUST run SCA vulnerability scanning for direct and transitive dependencies.
- **MUST:** The project MUST define a vulnerability policy (time-to-fix and gating thresholds) in the Master Doc, including:
  - how severity is determined (e.g., CVSS),
  - which severities block releases,
  - waiver / exception process (with expiry).

#### 6.3.4 Artifact signing and provenance (recommended; required for L2)

- **SHOULD:** Sign release artifacts (container images, packages) and verify signatures during deployment.
- **MUST (L2):** The deployment system MUST verify signatures (admission control or equivalent) and SHOULD capture provenance metadata (builder identity, source revision).

#### 6.3.5 Base image and toolchain pinning (required)

- **MUST:** Base images and build environments MUST be pinned (digest or equivalent).
- **MUST NOT:** Use floating tags (`latest`) for production build/deploy images.

#### 6.3.6 Secrets hygiene (recommended)

- **SHOULD:** Repos SHOULD run secret scanning (pre-commit and CI) over git history.
- **MUST:** If a secret leak is detected, rotation MUST be treated as an incident with documented remediation.

---


## 7. Migrations across deploy boundaries

This section applies to any persisted/external surface where mixed versions exist.

### 7.1 Database migrations

- **MUST:** Use expand/contract patterns for schema migrations when rollouts can observe mixed versions.
- **MUST:** Backward- and forward-compatible windows MUST be documented.
- **SHOULD:** Prefer additive columns/tables first, then switch writers/readers, then remove legacy.

### 7.2 Cache migrations

- **MUST:** Cache keys MUST be versioned when payload format changes.
- **SHOULD:** Prefer writing new keys alongside old keys during migration windows.

### 7.3 Queue/event migrations

- **MUST:** Message schemas are contracts and MUST be fixture-backed.
- **MUST:** Consumers MUST tolerate unknown fields.

---

## 8. External dependencies and vendor integration

### 8.1 Dependency Registry (required for L1/L2)

**MUST (L1/L2):** Maintain a Dependency Registry containing, at minimum:

| Dependency | Type | Purpose | Contract surface | Auth | Rate limits | Cost model | Data policy | SLA/SLO | Fallback | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Rules:

- **MUST:** Every dependency MUST have an owner and an escalation path.
- **MUST:** Vendor failure modes MUST be documented (timeouts, throttling, partial outages).
- **SHOULD:** CI SHOULD avoid live dependency calls; use stubs/snapshots.

### 8.2 Contracting and change control

- **SHOULD (L2):** L2 programs SHOULD require vendor-change notifications and a review process for API changes.
- **MUST:** If a vendor is a single point of failure, the system MUST have a defined degraded mode.

---

## 9. AI service providers and model operations

### 9.1 Provider integration as a contract surface

- **MUST:** Calls to LLM/AI services MUST be wrapped behind explicit interfaces with:
  - request/response logging policy,
  - redaction rules,
  - timeout and retry rules,
  - rate-limit handling.
- **MUST:** Prompt identifiers (`promptId`), model identifiers (`modelId`), and tool schemas MUST be versioned and traceable.

### 9.2 Provider portability (recommended)

- **SHOULD:** Systems SHOULD support at least one fallback strategy:
  - model fallback (same provider),
  - provider fallback (multi-provider),
  - or partial offline behavior.

### 9.3 Data handling

- **MUST:** The project MUST declare whether user data is sent to providers, retained, or used for training, aligned with vendor policy and your compliance constraints.

---

## 10. Observability, SLOs, and incident response

### 10.1 Minimum observability

- **MUST:** Production systems MUST emit logs, metrics, and traces sufficient to debug cross-boundary failures.
- **MUST:** Correlation IDs (`requestId`, `traceId`, `runId`) MUST be propagated across boundaries.

### 10.2 Runbooks and on-call

- **MUST (L1/L2):** There MUST be runbooks for deploy, rollback, and key incident classes.
- **MUST (L2):** L2 programs MUST have an on-call and incident response process documented.

### 10.3 Post-incident learning

- **SHOULD:** Significant incidents SHOULD produce a postmortem with tracked remediation items.

---

## 11. Release strategies

Projects MAY use rolling, blue/green, canary, or other strategies.

Rules:

- **MUST:** The chosen strategy MUST be documented and consistent with compatibility-mode requirements.
- **MUST:** Rollback constraints MUST be explicit.
- **SHOULD:** For risky changes, prefer canary + feature flags.

---

## 12. Enterprise / government-scale extensions (L2 guidance)

Large municipal or enterprise programs (e.g., “digital city” platforms) have additional realities: multi-tenant data governance, many vendors, many teams, and formal audit.

**MUST (L2 large programs):** In addition to the baseline requirements above, programs MUST define:

- **Service catalog + ownership** (who owns each service/API)
- **API governance** (gateway, versioning policy, deprecation windows)
- **Identity and access** (SSO, RBAC/ABAC, least privilege)
- **Audit logging** (who did what, when)
- **Change management** (release calendar, CAB-like process when required)
- **Data governance** (classification, residency, retention, sharing agreements)
- **Vendor management** (SLA tracking, escalation, contract renewals)

Programs SHOULD also define:

- multi-region strategy and disaster recovery (RTO/RPO),
- central observability standards,
- shared platform libraries and golden paths.

---

## 13. Required artifacts checklist (L1/L2)

A project adopting DAS-Deploy SHOULD be able to point to:

- Environment Matrix
- Deployment Pipeline description
- Dependency Registry
- Secrets + rotation runbooks
- Migration strategy notes (DB/cache/queue)
- Observability and SLOs
- Rollback plan

These artifacts MAY live inside the Master Doc set or as linked sub-docs, but they MUST be versioned and reviewed with code.


---

## 14. Templates (copy/paste)

### 14.1 Environment Matrix (template)

```md
## Environment Matrix

| Environment | Purpose | Data class allowed | Secrets strategy | External deps mode | Deploy method | Rollback | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- |
| local | dev machine | synthetic only | .env + local vault | stubbed | docker compose | git reset | <team> |
| dev | feature testing | synthetic/masked | secrets manager | mixed | CI deploy | redeploy | <team> |
| staging | RC validation | masked | secrets manager | prod-like | promotion | rollback + runbook | <team> |
| prod | real users | production | secrets manager + rotation | production | promotion | incident process | <team> |
```

### 14.2 Dependency Registry (template)

```md
## Dependency Registry

| Dependency/Vendor | Type | Purpose | Contract surface | Auth | Rate limits | Data policy | SLA/SLO | Fallback | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <OpenAI/LLM> | AI API | text generation | <tool spec / API IDs> | API key | <...> | <PII policy> | <...> | <provider switch / degrade> | <team> |
| <Cloud DB> | managed DB | storage | <schema IDs> | IAM | n/a | <...> | <...> | <backup/restore> | <team> |
```

### 14.3 Deployment Pipeline (template)

```md
## Deployment Pipeline

- Build system: <CI provider>
- Artifact: <image/package>
- Provenance: <SBOM/signing>
- Promotion: <same artifact or rebuild>
- Gates:
  - PR: <verify>
  - Nightly: <verify --full>
  - Pre-prod: <smoke + compat>
- Migrations:
  - DB: <expand/contract>
  - Cache/queue: <compat window>
- Rollback:
  - Safe rollback? <Y/N> (explain)
  - Procedure: <link runbook>
```

### 14.4 Runbook skeleton (template)

```md
## Runbook: <topic>

- Purpose:
- Preconditions:
- Safety checks:
- Step-by-step procedure:
- Rollback / undo:
- Verification:
- Escalation:
- Links (dashboards, logs, alerts):
```

### 14.5 Release readiness checklist (template)

```md
## Release readiness

- [ ] Environment Matrix updated
- [ ] Dependency Registry updated
- [ ] Contract changes classified (additive/breaking) + compat plan
- [ ] Migrations reviewed + rollback constraints documented
- [ ] Alerts and dashboards exist for key SLOs
- [ ] Runbooks exist (deploy/rollback/key incidents)
- [ ] Security review completed (if required)
- [ ] Cost budgets reviewed (AI + cloud)
```
