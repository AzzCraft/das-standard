#!/usr/bin/env bash
# DAS-06-013 - delegate to the canonical suite image scan wrapper.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec "$ROOT_DIR/das-suite/scripts/security/image_scan.sh" "$@"
