#!/usr/bin/env bash
# DAS-06-012 - delegate to the canonical suite OSV scanner wrapper.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec "$ROOT_DIR/das-suite/scripts/security/osv_scan.sh" "$@"
