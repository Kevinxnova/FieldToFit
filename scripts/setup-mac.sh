#!/bin/bash
# Compatibility entry point; implementation is grouped by purpose.
set -euo pipefail
exec bash "$(cd "$(dirname "$0")" && pwd)/setup/macos.sh" "$@"
