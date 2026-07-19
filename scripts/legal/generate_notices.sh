#!/usr/bin/env bash
# DAS-06-005 - delegate to the canonical suite notice generator.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
REPO_DIR="$ROOT_DIR/das-standard"
if [[ "$#" -eq 0 ]]; then
  exec "$ROOT_DIR/das-suite/scripts/legal/generate_notices.sh" "$REPO_DIR" "$REPO_DIR/THIRD_PARTY_NOTICES.md"
fi
exec "$ROOT_DIR/das-suite/scripts/legal/generate_notices.sh" "$@"
