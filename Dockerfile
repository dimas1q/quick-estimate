# Стадия 1 — Сборка frontend
FROM node:20 AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend .
RUN npm run build

# Стадия 2 — Backend + wkhtmltopdf + встроенный frontend
FROM python:3.11-slim AS app
WORKDIR /app

# Установим системные зависимости для wkhtmltopdf
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей Python
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем backend и frontend
COPY backend /app/backend
COPY --from=frontend-builder /app/dist /app/backend/app/frontend

WORKDIR /app/backend

# Старт без hot-reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
