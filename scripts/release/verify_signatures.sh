#!/usr/bin/env bash
# DAS-06-009 - delegate to the canonical suite signature verification gate.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec "$ROOT_DIR/das-suite/scripts/release/verify_signatures.sh" "$@"
