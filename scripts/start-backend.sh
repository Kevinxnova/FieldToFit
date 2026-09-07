#!/bin/bash
# Compatibility entry point; implementation is grouped by purpose.
set -euo pipefail
exec bash "$(cd "$(dirname "$0")" && pwd)/runtime/start-backend.sh" "$@"
