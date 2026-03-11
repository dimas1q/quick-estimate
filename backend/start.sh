#!/bin/bash
set -e

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_WAIT_TIMEOUT="${DB_WAIT_TIMEOUT:-60}"
RELOAD_FLAG="${1:-}"

echo "⏳ Ожидание доступности PostgreSQL (${DB_HOST}:${DB_PORT})..."
for i in $(seq 1 "${DB_WAIT_TIMEOUT}"); do
  if python - "${DB_HOST}" "${DB_PORT}" <<'PY'
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])

s = socket.socket()
s.settimeout(1.0)
try:
    s.connect((host, port))
except OSError:
    sys.exit(1)
finally:
    s.close()
PY
  then
    echo "✅ PostgreSQL доступен"
    break
  fi

  if [ "${i}" -eq "${DB_WAIT_TIMEOUT}" ]; then
    echo "❌ PostgreSQL не стал доступен за ${DB_WAIT_TIMEOUT} секунд"
    exit 1
  fi

  sleep 1
done

echo "🛠  Применяем миграции Alembic..."
alembic upgrade head

echo "🚀 Запускаем Uvicorn..."
if [ "${RELOAD_FLAG}" = "--reload" ]; then
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
