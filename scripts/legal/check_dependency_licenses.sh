#!/usr/bin/env bash
# DAS-06-006 - delegate to the canonical suite dependency license checker.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec "$ROOT_DIR/das-suite/scripts/legal/check_dependency_licenses.sh" "$@"
