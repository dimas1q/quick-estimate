# QuickEstimate

QuickEstimate — веб-приложение для управления сметами (FastAPI + Vue 3 + PostgreSQL + Docker).

## Текущее состояние (на 11 марта 2026)

### Реализовано
- JWT-аутентификация (логин/регистрация) + email OTP-активация аккаунта.
- CRUD для смет, шаблонов и клиентов.
- Позиции сметы: количество, единица, внутренняя/внешняя цена, категории, подсчёт итогов.
- НДС (вкл/выкл + ставка) и расчёт итоговой суммы с НДС.
- История изменений (change logs), избранные сметы.
- Версионирование смет (снимки + восстановление, с ограничениями).
- Экспорт сметы в PDF/Excel.
- Аналитика на backend + визуализация на frontend.
- Docker Compose для dev/prod окружения.

### Не реализовано / реализовано частично
- OAuth (Google/GitHub и т.д.) отсутствует.
- Полноценный admin-контур (управление пользователями/ролями) отсутствует.
- Отправка сметы клиенту по email с настраиваемым текстом/вложением отсутствует.
- Скидки по позициям (процент/фикс) отсутствуют.
- Read-only режим сметы отсутствует.
- Автосохранение черновика отсутствует.
- Полноценный flow «создать смету из шаблона» отсутствует (есть добавление позиций из шаблона).
- Импорт через backend endpoint отсутствует (импорт в основном фронтовый).
- Клонирование шаблонов отдельной операцией отсутствует.
- NGINX/CI-CD pipeline в репозитории отсутствуют.

## Стек
- Backend: FastAPI, SQLAlchemy (async), Alembic, Pydantic, JWT.
- Frontend: Vue 3, Pinia, Vue Router, Tailwind CSS, Vite.
- DB: PostgreSQL 14.
- Infra: Docker, Docker Compose, Mailhog (dev SMTP).

## Структура
- `backend/` — API, модели, схемы, миграции, экспорт PDF/Excel.
- `frontend/` — SPA на Vue 3, страницы, компоненты, Pinia stores.
- `docker-compose.yml` — dev-стек (`backend`, `frontend`, `db`, `mailhog`).
- `docker-compose.prod.yml` — prod-стек (`app`, `db`, `mailhog`).
- `Dockerfile` — мультистейдж сборка frontend + backend в одном контейнере.

## Запуск

### Dev (рекомендуется)
```bash
docker compose up --build
```

Сервисы:
- Frontend: `http://localhost:5173`
- API: `http://localhost:8000/api`
- Mailhog UI: `http://localhost:8025`

### Prod compose
```bash
docker compose -f docker-compose.prod.yml up --build -d
```

## Локальная разработка без Docker

### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Проверка состояния сборки
- `python3 -m compileall backend/app` — проходит успешно.
- `frontend: npm ci` — падает из-за рассинхронизации `package.json` и `package-lock.json` (ошибка EUSAGE).
- Автотесты в репозитории не обнаружены.

## Известные технические риски
- Миграции Alembic в неконсистентном состоянии (ветвление истории + dev seed migration как актуальный head).
- Одновременно используются Alembic и `Base.metadata.create_all()` на старте приложения.
- `DATABASE_URL` захардкожен в `backend/app/core/database.py`.
- CORS ограничен `http://localhost:5173` в `backend/app/main.py`.
- Восстановление версии сметы в `backend/app/api/versions.py` восстанавливает не все поля модели.
- В формах выбора клиентов/шаблонов загружается только первая страница (backend default `limit=5`).
- Баг фильтра по статусу в `frontend/src/pages/estimate/EstimatesPage.vue` (статус сериализуется как массив символов).

## Лицензия
PolyForm Noncommercial License 1.0.0 (`LICENSE`, `NOTICE`).
