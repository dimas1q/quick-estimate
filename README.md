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
- Docker: separate `backend/Dockerfile` (Python 3.11 + wkhtmltopdf) and `frontend/Dockerfile` (Node 20); `docker-compose.yml` for dev stack
- Data persistence: PostgreSQL 14 (service `db`), volume `pgdata`; JWT secret stored at `config/secret.key` (mounted from `data/`)

## Requirements
- Python 3.11, Node.js 20, npm
- PostgreSQL 14
- wkhtmltopdf available on host if running backend outside Docker
- Docker + Docker Compose (recommended for dev/prod)

## Quick Start (local)
Recommended path is the dev Docker Compose stack.

```bash
docker compose up --build
# frontend: http://localhost:5173
# api:      http://localhost:8000/api
```

Notes:
- Backend binds to 0.0.0.0:8000 and expects PostgreSQL at host `db` with user/password `postgres` / DB `quickestimate`.
- CORS allows `http://localhost:5173`.
- JWT secret is auto-created at `config/secret.key` (persisted via `data/` volume).

## Docker
- Dev stack: `docker compose up --build` (services: `backend`, `frontend`, `db`)
- Prod compose: `docker compose -f docker-compose.prod.yml up --build -d`  
  The prod file expects a monolithic `Dockerfile` at repo root (not present); either add one or point it to the existing `backend/Dockerfile` and ship built frontend assets into `backend/app/frontend`.

## Configuration
Environment:

| Variable | Default | Scope | Description |
| --- | --- | --- | --- |
| `POSTGRES_DB` | `quickestimate` | Docker compose | Database name |
| `POSTGRES_USER` | `postgres` | Docker compose | Database user |
| `POSTGRES_PASSWORD` | `postgres` | Docker compose | Database password |
| `VITE_API_URL` | `http://localhost:8000/api` (dev), `/api` (prod) | frontend | API base URL used by Axios |

Other config:
- Backend DB URL is hardcoded to `postgresql+asyncpg://postgres:postgres@db/quickestimate` (`backend/app/core/database.py`). If running without Docker, ensure the host `db` resolves or adjust that file.
- JWT secret stored/read from `config/secret.key` (auto-generated if missing).

## Usage
- Backend (manual):  
  ```bash
  cd backend
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  alembic upgrade head  
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  ```
- Frontend (manual):  
  ```bash
  cd frontend
  npm install
  cp .env.development .env 
  npm run dev -- --host
  ```
- API base path: `/api`. Authorization via `Authorization: Bearer <token>`.


## Troubleshooting
- Backend cannot connect to DB outside Docker: either run Postgres as `db` host or update `backend/app/core/database.py`.
- PDF export fails: install `wkhtmltopdf` on host or run inside the backend Docker image.
- CORS errors: ensure the frontend origin matches the allowed origin (`http://localhost:5173` by default) or adjust middleware in `app/main.py`.
- Prod compose build fails: supply a root `Dockerfile` or point to existing backend Dockerfile and include built frontend assets under `backend/app/frontend`.

## License
PolyForm Noncommercial License 1.0.0 (see `LICENSE` and `NOTICE` for non-commercial and attribution terms).
