You are implementing code in a DAS-standard compliant product repo.

Key rules:
- Serialized contracts use camelCase (e.g. `runId`, `configHash`, `pipelineResult`).
- All cross-boundary envelope shapes must include `schemaVersion`.
- Error responses use ErrorEnvelope: `{code, kind, message, retryable, details, correlation}`.
- Diagnostics are bounded and structured: `{codes[], kv{}, counters{}}`.
- Budget tracking uses allocated/consumed/remaining ledger pattern.
- All identifiers must be stable across serialization cycles.

When producing JSON artifacts, ensure camelCase field names and include schemaVersion.
