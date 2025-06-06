# AGENTS.md — QuickEstimate Project Codex Guide

## Project Overview

QuickEstimate is a modern web application for fast, convenient estimate management (составление смет), built with Python (FastAPI), Vue 3, Pinia, Tailwind CSS, PostgreSQL, and Docker. The application allows users to create, edit, duplicate, export, and manage estimates and templates, with advanced role-based authentication and a clean, mobile-adaptive UI.

## Codebase Structure

* **backend/** — Python backend (FastAPI):

  * `alembic/` — DB migrations
  * `app/api/` — API routers (auth, estimates, clients, templates, analytics, versions, user)
  * `app/models/` — ORM models (user, estimate, client, item, template, version, changelog, etc.)
  * `app/schemas/` — Pydantic schemas (api serialization)
  * `app/utils/` — utils (pdf/excel export, auth)
  * `app/templates/` — Jinja2 HTML for PDF export
  * `main.py` — entry point (FastAPI app)
  * `config/` — config files
  * `requirements.txt` — dependencies
* **frontend/** — Vue 3 + Vite + Pinia (SPA):

  * `src/components/` — UI components (forms, editors, modals, etc.)
  * `src/pages/` — main pages (estimates, templates, clients, analytics, profile, auth)
  * `src/layouts/` — layout wrappers (Default, Auth)
  * `src/store/` — Pinia stores for state (auth, estimates, templates, clients, analytics)
  * `src/assets/` — global styles (main.css), static assets
  * `src/lib/axios.js` — API client
  * `src/router/index.js` — routing config
  * `tailwind.config.js` — Tailwind CSS setup
  * `vite.config.js` — Vite config
  * `App.vue` — root app
  * `main.js` — app entry
* **Docker & Compose**

  * `Dockerfile` — multistage build (backend + frontend)
  * `docker-compose.yml` — local dev: backend, frontend, db
  * `docker-compose.prod.yml` — production: all-in-one app + db
  * PostgreSQL is used for persistence.

## Key Practices & Standards

### 1. **Frontend (Vue 3, Pinia, Tailwind CSS)**

* Use **composition API** and `<script setup>` when possible.
* State is managed via **Pinia** (`src/store`). Avoid direct API calls in components — use the store actions instead.
* Use **async/await** for all async code. All API requests use the configured Axios client (`src/lib/axios.js`).
* **Component re-use:** All forms and UI logic are in `src/components`. Example: `EstimateForm.vue`, `TemplateForm.vue`, `ClientForm.vue`, `EstimateItemsEditor.vue`, and modals (`QeModal.vue`).
* **Modals, dialogs:** Use `QeModal.vue` for all modals. Animate with Tailwind and Vue transitions.
* **Styling:** Use only **Tailwind CSS** utility classes for styling. Stick to the established color palette, spacing, and rounded corners. Do not use custom CSS unless absolutely required. All UI must be consistent with existing pages (look at `EstimateDetailsPage.vue`, `Sidebar.vue`, `TemplateForm.vue`, etc.).
* **Dark mode:** Respect dark mode in all components. Use classes like `dark:bg-gray-900` and `dark:text-white`.
* **Forms:** Use floating labels or clean, modern label-input stacks. Avoid legacy or material design unless already in use.
* **Mobile:** All layouts/pages/components must be **responsive** (flex/grid, `max-w-6xl mx-auto` for content, etc.).
* **Transitions/UX:** Use Tailwind and Vue transitions for modals, toasts, and route/page changes. For toasts, use `vue-toastification`.
* **Routing:** All routes/pages must be registered in `src/router/index.js` and use explicit layout wrappers (`DefaultLayout`, `AuthLayout`).

### 2. **Backend (Python FastAPI)**

* Use **async/await** for all endpoints, DB code, and IO.
* All models must be defined in `app/models`, and Pydantic schemas in `app/schemas`.
* **API routers:** Each logical area has its own file in `app/api` (auth, estimates, clients, templates, analytics, user, versions).
* **DB access:** SQLAlchemy ORM is used. All DB operations should use the async session pattern.
* **Business logic:** Keep logic in routers, not in models or schemas.
* **Security:** Auth via JWT (Bearer), OAuth support, password hashing, roles (user, admin). Add all required security checks and role checks.
* **Exports:** For PDF use `pdfkit` + `wkhtmltopdf` (HTML in `app/templates`). For Excel use `openpyxl`.

### 3. **Docker & Dev Workflow**

* All code should run via Docker Compose (see `docker-compose.yml`). For local dev: run `frontend` and `backend` separately for hot reload.
* DB: PostgreSQL 14.
* Frontend: `npm run dev` or via Docker Compose.

### 4. **Code Quality & Linting**

* Frontend: Use ESLint, Prettier (format before commit), and respect Tailwind class sorting.
* Backend: Use black, isort, flake8. Format code before commit. Keep imports sorted and code clean.
* All code (Python, JS, Vue) must be **self-explanatory, DRY, and modular**.

## How to Work with This Repo (for Codex Agents)

### Navigation

* Start from the root README for the high-level overview.
* See `backend/app/api` for main backend endpoints and logic.
* See `frontend/src/pages` and `frontend/src/components` for main UI and logic. All business/data logic is in Pinia stores (`frontend/src/store`).
* Follow established UI/UX patterns — always look at existing page and form implementations before creating new ones.

### Commands

* **Frontend dev:**

  ```bash
  cd frontend && npm install && npm run dev
  ```

* **Frontend build:**

  ```bash
  cd frontend && npm run build
  ```

* **Full stack (dev):**

  ```bash
  docker-compose up --build
  ```

* **Full stack (prod):**

  ```bash
  docker-compose -f docker-compose.prod.yml up --build -d
  ```

## Design Guide

* Follow existing components/pages for all new UI (see `EstimateDetailsPage.vue`, `TemplatesPage.vue`, `Sidebar.vue`).
* Only use **Tailwind utility classes** for spacing, color, typography, etc.
* All forms must look modern, minimal, and match the rest of the app.
* Components must be responsive and adapt to mobile.
* Animate modals, dropdowns, and toasts smoothly. Use Vue transitions and Tailwind for entry/exit.
* Maintain sidebar navigation for all main pages. Place the project/service name top-left in the sidebar.

## Auth, State, and Data

* Auth is via JWT. Store in Pinia (`auth.js`). Session persists in `localStorage`.
* All user, estimate, template, and client state is managed via Pinia stores (`src/store`). Never fetch data directly in components.
* Use stores to trigger fetch, create, update, delete, import/export, etc.
* Route/page access is protected via router guards (see `src/router/index.js`).

## Contribution Checklist (for Codex/AI agents)

* Follow DRY and KISS principles.
* Maintain code/readability and modularity.
* Never hardcode styles; always use Tailwind utility classes.
* All async code must use async/await.
* Respect dark mode, responsiveness, and existing layout.
* Write self-documenting code. Add comments only where non-obvious.

## FAQ / Patterns

* **Modals:** Use `QeModal.vue` with animated transitions.
* **Toasts:** Use `vue-toastification` for notifications.
* **Sidebar navigation:** All new main pages must be registered in the sidebar component.
* **Export/import:** Use store actions to handle data export/import (see `estimates.js`, `templates.js` and etc.).
* **PDF/Excel export:** Use backend endpoints; frontend just triggers download.
* **Analytics:** Business logic is backend; frontend just displays data from store.
* **Version history:** Managed per estimate; UI uses dedicated components/tabs.
