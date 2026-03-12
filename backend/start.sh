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
print(settings.LOG_DATE_FORMAT)
print(",".join(settings.LOG_LEVELS))
print("1" if settings.LOG_USE_COLOR else "0")
PY
); then
  echo "❌ Failed to load application settings"
  exit 1
fi

if [ "${#APP_CFG[@]}" -lt 12 ]; then
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
CFG_LOG_DATE_FORMAT="${APP_CFG[9]}"
CFG_LOG_LEVELS="${APP_CFG[10]}"
CFG_LOG_USE_COLOR="${APP_CFG[11]}"

DB_HOST="${DB_HOST:-${CFG_DB_HOST}}"
DB_PORT="${DB_PORT:-${CFG_DB_PORT}}"
DB_WAIT_TIMEOUT="${DB_WAIT_TIMEOUT:-${CFG_DB_WAIT_TIMEOUT}}"
SERVER_HOST="${SERVER_HOST:-${CFG_SERVER_HOST}}"
SERVER_PORT="${SERVER_PORT:-${CFG_SERVER_PORT}}"

RUNTIME_CONFIG_PATH="${FRONTEND_RUNTIME_CONFIG_PATH:-${CFG_RUNTIME_CONFIG_PATH}}"
FRONTEND_API_URL="${FRONTEND_API_URL:-${CFG_FRONTEND_API_URL}}"
FRONTEND_GOOGLE_CLIENT_ID="${FRONTEND_GOOGLE_CLIENT_ID:-${CFG_FRONTEND_GOOGLE_CLIENT_ID}}"
LOG_DATE_FORMAT="${LOG_DATE_FORMAT:-${CFG_LOG_DATE_FORMAT}}"
LOG_LEVELS="${LOG_LEVELS:-${CFG_LOG_LEVELS}}"
LOG_USE_COLOR="${LOG_USE_COLOR:-${CFG_LOG_USE_COLOR}}"

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

UVICORN_LOG_CONFIG_PATH="${UVICORN_LOG_CONFIG_PATH:-/tmp/quickestimate-uvicorn-log.json}"
"${PYTHON_BIN}" - "${UVICORN_LOG_CONFIG_PATH}" "${LOG_LEVELS}" "${LOG_DATE_FORMAT}" "${LOG_USE_COLOR}" <<'PY'
import json
import pathlib
import sys

config_path = pathlib.Path(sys.argv[1])
levels_raw = sys.argv[2]
date_format = sys.argv[3]
use_color = sys.argv[4] == "1"

levels = [chunk.strip().upper() for chunk in levels_raw.split(",") if chunk.strip()]
if not levels:
    levels = ["INFO", "ERROR"]

payload = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "allow_selected_levels": {
            "()": "app.core.logging.LevelAllowlistFilter",
            "levels": levels,
        }
    },
    "formatters": {
        "matrix": {
            "()": "app.core.logging.MatrixFormatter",
            "use_color": use_color,
            "datefmt": date_format,
        }
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "matrix",
            "filters": ["allow_selected_levels"],
            "stream": "ext://sys.stdout",
        },
        "access": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "matrix",
            "filters": ["allow_selected_levels"],
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "DEBUG", "propagate": False},
        "uvicorn.error": {"handlers": ["default"], "level": "DEBUG", "propagate": False},
        "uvicorn.access": {"handlers": ["access"], "level": "DEBUG", "propagate": False},
    },
    "root": {"handlers": ["default"], "level": "DEBUG"},
}

config_path.parent.mkdir(parents=True, exist_ok=True)
config_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
PY

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
alembic -q upgrade head

echo "🚀 Starting Uvicorn..."
if [ "${1:-}" = "--reload" ] || [ "${CFG_SERVER_RELOAD}" = "1" ]; then
  exec uvicorn app.main:app --host "${SERVER_HOST}" --port "${SERVER_PORT}" --reload --log-config "${UVICORN_LOG_CONFIG_PATH}"
fi

exec uvicorn app.main:app --host "${SERVER_HOST}" --port "${SERVER_PORT}" --log-config "${UVICORN_LOG_CONFIG_PATH}"
