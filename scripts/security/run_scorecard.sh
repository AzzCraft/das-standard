#!/usr/bin/env bash
# DAS-06-011 - delegate to the canonical suite OpenSSF Scorecard runner.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec "$ROOT_DIR/das-suite/scripts/security/run_scorecard.sh" "$@"
