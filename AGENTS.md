# AGENTS.md — QuickEstimate (актуализировано на 11.03.2026)

## 1) Краткий контекст проекта

QuickEstimate — FastAPI + Vue 3 приложение для смет (не Flask).

Стек:
- Backend: FastAPI, async SQLAlchemy, Alembic, JWT, Pydantic.
- Frontend: Vue 3, Pinia, Vue Router, Tailwind, Vite.
- DB/infra: PostgreSQL 14, Docker Compose, Mailhog.

## 2) Реальное состояние функционала

### Реализовано
- Email/password auth + OTP-активация, JWT.
- CRUD: сметы, шаблоны, клиенты.
- История изменений (logs), избранное.
- Версии смет (создание снимков, restore с ограничениями).
- Экспорт смет: PDF/Excel.
- Аналитика (backend + frontend отображение).

### Частично или отсутствует
- OAuth-провайдеров нет.
- Полноценного admin-контура нет (хотя `is_admin` в модели есть).
- Скидки по позициям нет.
- Read-only режим сметы нет.
- Autosave черновиков нет.
- Email-отправка смет клиенту нет (email используется для OTP).
- Полноценного мастера «создать смету из шаблона» нет.
- Backend import endpoint для смет/шаблонов нет (импорт в основном фронтовый).
- Клонирования шаблона отдельным endpoint нет.
- NGINX/CI-CD в репозитории нет.

## 3) Структура репозитория

- `backend/`
  - `app/api/`: `auth`, `user`, `estimates`, `templates`, `clients`, `versions`, `analytics`, `notes`
  - `app/models/`, `app/schemas/`, `app/utils/`, `app/templates/`
  - `alembic/versions/` миграции
- `frontend/`
  - `src/pages/`, `src/components/`, `src/store/`, `src/router/`
  - `src/lib/axios.js`
- infra
  - `docker-compose.yml` (dev)
  - `docker-compose.prod.yml` (prod)
  - root `Dockerfile` (multistage: frontend build + backend runtime)

## 4) Ключевые риски, которые нужно учитывать при изменениях

- Alembic-цепочка миграций неконсистентна (ветвления + merge/seed история).
- На старте backend вызывается `create_all()` параллельно с миграционным подходом.
- `DATABASE_URL` захардкожен в `backend/app/core/database.py`.
- CORS зафиксирован на `http://localhost:5173`.
- Restore версий смет восстанавливает не все поля.
- В UI выбор клиентов/шаблонов может быть неполным из-за backend default `limit=5`.
- В `EstimatesPage.vue` есть баг фильтра статуса (строка статуса превращается в массив символов).
- Автотестов нет.

## 5) Правила для агентских изменений

### Frontend
- Использовать Pinia store actions для API; не дублировать HTTP-вызовы в компонентах.
- Предпочитать Composition API и `<script setup>`.
- Стилизация через Tailwind utility classes; сохранять existing UI/UX паттерны.
- Учитывать dark mode и адаптивность.

### Backend
- Использовать async/await для endpoint-ов и DB операций.
- Проверять авторизацию и user ownership в каждом endpoint.
- Согласовывать изменения моделей с миграциями Alembic.

## 6) Проверка изменений

Минимум перед сдачей:
```bash
python3 -m compileall backend/app
```

Важно по frontend:
- На текущем состоянии `npm ci` падает (lockfile mismatch).
- При необходимости локальной работы использовать `npm install` как временный обходной путь, но помнить, что lockfile требует нормализации.

## 7) Команды

Dev стек:
```bash
docker compose up --build
```

Prod стек:
```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Локально frontend:
```bash
cd frontend
npm install
npm run dev
```

Локально backend:
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
