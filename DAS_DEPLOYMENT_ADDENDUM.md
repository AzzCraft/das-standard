# DAS Deployment Addendum

> Status: normative addendum to the DAS Standard for deployment-time concerns.
> Applies to: any product claiming DAS Tools conformance.

This addendum specifies the deployment-time controls a DAS-conformant
product MUST implement, in addition to the design and build controls in
the core standard.

## 1. Identity & Trust Roots

1.1. The product MUST ship with a documented **trust root** (TUF root, set
of cosign keys, or HSM-backed CA). The trust root MUST be rotatable
without re-installing the product.

1.2. Each release artifact MUST be signed and the signature MUST be
verifiable using only the trust root and metadata distributed via the
update channel.

## 2. Configuration Hygiene

2.1. Secrets MUST NOT appear in image layers, Helm values, or
`docker-compose.yml` files. They MUST be injected via:
  - Kubernetes `Secret` objects (referenced via `existingSecret`), OR
  - Docker Compose `secrets:` blocks backed by external files, OR
  - Cloud secret managers (AWS Secrets Manager, GCP Secret Manager, Vault).

2.2. Default credentials are FORBIDDEN. The product MUST refuse to start
without explicit administrator-provided credentials.

## 3. Network Posture

3.1. All cross-component traffic MUST be TLS 1.2+ with strong cipher
suites. Plain HTTP is permitted only on `/healthz` listening on
loopback or within an isolated namespace.

3.2. Helm charts MUST ship with a `NetworkPolicy` that defaults to deny
all ingress except documented ports.

## 4. Observability

4.1. The product MUST emit structured logs with redaction of PII and
secrets (see `shared/logging/redaction.py`).

4.2. The product MUST expose Prometheus metrics under `/metrics`,
including the standard DAS counters: `das_verifications_total`,
`das_audit_events_total`, `das_hashchain_violations_total`,
`das_license_state`.

4.3. A reference dashboard or equivalent machine-readable metrics view MUST be
provided by the adopting project.

## 5. Backup & Restore

5.1. The product MUST ship `backup.sh` and `restore.sh` scripts with a
documented manifest format, OR provide an equivalent operator/CRD.

5.2. Restore MUST be deterministic: a restored deployment MUST verify
identically to the source under `dassuite verify-all`.

## 6. Air-gapped Operation

6.1. The product MUST support installation from an air-gapped bundle
produced by `make_airgap_bundle.sh`.

6.2. The bundle MUST contain a TUF metadata snapshot or equivalent so
the air-gapped operator can verify subsequent updates without internet
access.

## 7. License Enforcement

7.1. The license file MUST be HMAC- or signature-verified before the
product becomes operational. Tampered or unrecognized licenses MUST
cause the product to enter `degraded` mode.

7.2. If an adopting project implements licensed features, its grace-period
rules MUST be explicit, testable, and local to that project's distribution.

## 8. Conformance Evidence

8.1. After deployment, the operator MUST be able to produce an
**EvidenceBundle** (`tools/evidence/verify_index.py`) covering:
  - the deployment topology,
  - the resolved trust root fingerprints,
  - the latest verification report,
  - the audit log root hash.

8.2. The EvidenceBundle is the artifact submitted to auditors and
relied upon by downstream consumers.

---

*Revision history is tracked in `CHANGELOG.md` and in the chapter index.*
