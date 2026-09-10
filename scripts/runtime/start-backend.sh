#!/bin/bash
# FieldToFit backend startup script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_DIR"

source .venv/bin/activate
if [ "${PYTHON_DOTENV_DISABLED:-0}" != "1" ] && [ -f .env ]; then
  set -a
  source .env
  set +a
fi

exec gunicorn --bind "${API_HOST:-127.0.0.1}:${API_PORT:-8000}" backend.api.main:app
