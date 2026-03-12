# QuickEstimate
FastAPI + Vue 3 application for building and tracking estimates with clients, templates, analytics, and export workflows.

## Features
- JWT authentication (login/register), profile update, and token persistence in `localStorage`
- Estimate lifecycle with items, VAT toggles, statuses, favorites, version history, and changelogs
- Client and template management with shared item library; notes on estimates/clients/templates
- Exports: PDF (wkhtmltopdf + Jinja2), Excel (openpyxl), CSV/PDF/Excel analytics
- Analytics: revenue/time-series breakdowns, category/responsible metrics, MoM/YoY growth
- Responsive Vue 3 SPA (Pinia, Vue Router, Tailwind, ApexCharts, Toastification) with dark-mode toggle

## Architecture / Project Structure
- `backend/` — FastAPI app (`app/main.py`) with async SQLAlchemy, Alembic migrations, JWT auth, PDF/Excel utilities  
  - `app/api/` routers: `auth`, `users`, `estimates`, `templates`, `clients`, `versions`, `analytics`, `notes`
  - `app/models/` ORM models: estimates, items, templates, clients, users, changelogs, favorites, versions, notes
  - `app/utils/` auth (bcrypt + jose), PDF (pdfkit/wkhtmltopdf), Excel exports, analytics Excel
  - `alembic/` migrations; `start.sh` applies migrations then runs Uvicorn
- `frontend/` — Vue 3 + Vite SPA with Pinia stores (`src/store`), routed pages under `src/pages`, Tailwind styles in `src/assets/main.css`
- Docker: separate `backend/Dockerfile` (Python 3.11 + wkhtmltopdf) and `frontend/Dockerfile` (Node 20)
- Configuration: TOML-first via `config/app.dev.toml` and `config/app.prod.toml`

## Requirements
- Python 3.11, Node.js 20, npm
- PostgreSQL 14
- wkhtmltopdf available on host if running backend outside Docker
- Docker + Docker Compose (recommended for dev/prod)

## Quick Start (local)
Recommended path for local development is `docker-compose.dev.yml`.

```bash
docker compose -f docker-compose.dev.yml up --build
# frontend: http://localhost:5173
# api:      http://localhost:8000/api
```

Notes:
- Backend runtime settings are loaded from TOML (`APP_CONFIG_FILE`), defaults are in `config/app.dev.toml`.
- Backend logging is configured in TOML (`[logging]`, `[logging.module_levels]`), startup emits Matrix-style boot banner with app name/version/mode.
- Frontend runtime settings are generated into `runtime-config.js` from the same TOML file.
  - `apiUrl` is derived automatically:
    - `development`: from `[server].port`
    - `production`: from `[app].domain`
  - `googleClientId` is derived from `[auth].google_oauth_client_id`
- On the first `alembic upgrade head`, a bootstrap admin user is created (if missing):
  - `login`: `admin`
  - `email`: `admin@quickestimate.app`
  - `password`: `admin12345`
- New users created via register/OAuth are regular users by default (`is_admin=false`).

## Docker
- Prod stack (default): `docker compose up --build -d` (uses `docker-compose.yml`)
- Dev stack: `docker compose -f docker-compose.dev.yml up --build`
- Make shortcuts:
  - `make up` - prod compose
  - `make dev` - dev compose
  - `make up dev` - dev compose (explicitly supported)
  - if `config/app.dev.local.toml` exists, dev commands use it automatically

## Configuration
Primary configuration source is TOML.

- Dev config: `config/app.dev.toml`
- Prod config: `config/app.prod.toml`
- Default system path (non-Docker/service mode): `/etc/quickestimate/app.toml`
- Repo fallback path: `config/app.toml`
- Frontend section is not required in TOML; frontend runtime config is auto-generated.
- Logging levels are TOML-driven; default allowlist is `INFO` and `ERROR` in both dev and prod.

Environment variables are now overrides only (for example `APP_CONFIG_FILE`, `DATABASE_URL`, `APP_DOMAIN`, `GOOGLE_OAUTH_CLIENT_ID`).

Security note:
- Do not commit JWT secrets into git.
- By default, backend stores generated JWT secret in the path from `auth.jwt_secret_key_path` (dev/prod defaults: `/app/config-runtime/secret.key` in Docker volumes).
- You can provide `JWT_SECRET_KEY` explicitly via environment for managed secret stores.

## Usage
- Backend (manual):  
  ```bash
  cd backend
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  export APP_CONFIG_FILE=/etc/quickestimate/app.toml
  alembic upgrade head  
  ./start.sh
  ```
- Frontend (manual):  
  ```bash
  cd frontend
  npm install
  export APP_CONFIG_FILE=/etc/quickestimate/app.toml
  npm run generate:runtime-config
  npm run dev -- --host
  ```
- API base path: `/api`. Authorization via `Authorization: Bearer <token>`.

## Admin Panel
- Administration routes:
  - `/admin/users` - users list, role updates, activation/deactivation
  - `/admin/users/:userId/workspace` - CRUD management of the selected user's clients, templates, and estimates
- Access to `/admin/*` is restricted to admin users (enforced in backend and frontend router guards).


## Troubleshooting
- Backend cannot connect to DB outside Docker: verify `/etc/quickestimate/app.toml` values (`[database]` and `[server]` sections).
- PDF export fails: install `wkhtmltopdf` on host or run inside the backend Docker image.
- CORS behavior is automatic:
  - `development`: `http://localhost:5173` and `http://127.0.0.1:5173`
  - origin from `[app].domain` is also allowed (if configured)

## License
PolyForm Noncommercial License 1.0.0 (see `LICENSE` and `NOTICE` for non-commercial and attribution terms).
