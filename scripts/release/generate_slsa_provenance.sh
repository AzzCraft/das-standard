#!/usr/bin/env bash
# DAS-06-007 - delegate to the canonical suite SLSA provenance generator.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec "$ROOT_DIR/das-suite/scripts/release/generate_slsa_provenance.sh" "$@"
