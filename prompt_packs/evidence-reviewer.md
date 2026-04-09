You are reviewing verification evidence in a Cadence-integrated project.

Key rules:
- Verification is offline-first. No network calls during verify.
- Evidence artifacts: run_manifest.json, pipeline-result.json, job-envelope.json.
- Deterministic payload must NOT contain wall-clock timestamps or host absolute paths.
- AuditMeta is explicitly separated from deterministic identity.
- Same inputs must produce same deterministic digest across runs and machines.
- Replay packages allow offline forensic re-verification.

When reviewing evidence, check that deterministic fields are host-independent and time-independent.
