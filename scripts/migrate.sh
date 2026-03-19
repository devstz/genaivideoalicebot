#!/usr/bin/env bash
# Применить миграции Alembic к БД API.
# Использование:
#   ./scripts/migrate.sh                    # из корня репо, с .venv и DATABASE_URL в .env
#   DATABASE_URL=postgresql+asyncpg://... ./scripts/migrate.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
else
  PY="${PYTHON:-python3}"
fi
exec "$PY" -m alembic upgrade head
