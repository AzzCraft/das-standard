#!/usr/bin/env bash
# DAS-06-014 - delegate to the canonical suite secret scan wrapper.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec "$ROOT_DIR/das-suite/scripts/security/secret_scan.sh" "$@"
