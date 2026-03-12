#!/bin/bash
set -e

PYTHON_BIN="python3"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

if ! readarray -t APP_CFG < <("${PYTHON_BIN}" - <<'PY'
from app.core.config import settings

print(settings.DB_WAIT_HOST)
print(settings.DB_WAIT_PORT)
print(settings.DB_WAIT_TIMEOUT)
print(settings.SERVER_HOST)
print(settings.SERVER_PORT)
print("1" if settings.SERVER_RELOAD else "0")
print(settings.FRONTEND_RUNTIME_CONFIG_PATH)
print(settings.FRONTEND_API_URL)
print(settings.FRONTEND_GOOGLE_CLIENT_ID)
PY
); then
  echo "❌ Failed to load application settings"
  exit 1
fi

if [ "${#APP_CFG[@]}" -lt 9 ]; then
  echo "❌ Incomplete settings payload received"
  exit 1
fi

CFG_DB_HOST="${APP_CFG[0]}"
CFG_DB_PORT="${APP_CFG[1]}"
CFG_DB_WAIT_TIMEOUT="${APP_CFG[2]}"
CFG_SERVER_HOST="${APP_CFG[3]}"
CFG_SERVER_PORT="${APP_CFG[4]}"
CFG_SERVER_RELOAD="${APP_CFG[5]}"
CFG_RUNTIME_CONFIG_PATH="${APP_CFG[6]}"
CFG_FRONTEND_API_URL="${APP_CFG[7]}"
CFG_FRONTEND_GOOGLE_CLIENT_ID="${APP_CFG[8]}"

DB_HOST="${DB_HOST:-${CFG_DB_HOST}}"
DB_PORT="${DB_PORT:-${CFG_DB_PORT}}"
DB_WAIT_TIMEOUT="${DB_WAIT_TIMEOUT:-${CFG_DB_WAIT_TIMEOUT}}"
SERVER_HOST="${SERVER_HOST:-${CFG_SERVER_HOST}}"
SERVER_PORT="${SERVER_PORT:-${CFG_SERVER_PORT}}"

RUNTIME_CONFIG_PATH="${FRONTEND_RUNTIME_CONFIG_PATH:-${CFG_RUNTIME_CONFIG_PATH}}"
FRONTEND_API_URL="${FRONTEND_API_URL:-${CFG_FRONTEND_API_URL}}"
FRONTEND_GOOGLE_CLIENT_ID="${FRONTEND_GOOGLE_CLIENT_ID:-${CFG_FRONTEND_GOOGLE_CLIENT_ID}}"

if [ -n "${RUNTIME_CONFIG_PATH}" ]; then
  "${PYTHON_BIN}" - "${RUNTIME_CONFIG_PATH}" "${FRONTEND_API_URL}" "${FRONTEND_GOOGLE_CLIENT_ID}" <<'PY'
import json
import pathlib
import sys

runtime_path = pathlib.Path(sys.argv[1])
api_url = sys.argv[2]
google_client_id = sys.argv[3]

runtime_path.parent.mkdir(parents=True, exist_ok=True)
payload = {
    "apiUrl": api_url,
    "googleClientId": google_client_id,
}
runtime_path.write_text(
    "window.__QE_CONFIG__ = Object.assign({}, window.__QE_CONFIG__ || {}, "
    + json.dumps(payload, ensure_ascii=False)
    + ");\n",
    encoding="utf-8",
)
PY
fi

echo "⏳ Waiting for PostgreSQL (${DB_HOST}:${DB_PORT})..."
for i in $(seq 1 "${DB_WAIT_TIMEOUT}"); do
  if "${PYTHON_BIN}" - "${DB_HOST}" "${DB_PORT}" <<'PY'
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])

sock = socket.socket()
sock.settimeout(1.0)
try:
    sock.connect((host, port))
except OSError:
    sys.exit(1)
finally:
    sock.close()
PY
  then
    echo "✅ PostgreSQL is reachable"
    break
  fi

  if [ "${i}" -eq "${DB_WAIT_TIMEOUT}" ]; then
    echo "❌ PostgreSQL was not reachable for ${DB_WAIT_TIMEOUT} seconds"
    exit 1
  fi

  sleep 1
done

echo "🛠  Running Alembic migrations..."
alembic upgrade head

echo "🚀 Starting Uvicorn..."
if [ "${1:-}" = "--reload" ] || [ "${CFG_SERVER_RELOAD}" = "1" ]; then
  exec uvicorn app.main:app --host "${SERVER_HOST}" --port "${SERVER_PORT}" --reload
fi

exec uvicorn app.main:app --host "${SERVER_HOST}" --port "${SERVER_PORT}"
