FROM node:20 AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend .
RUN npm run build

FROM python:3.11-slim-bookworm AS app
WORKDIR /app

RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app/backend
COPY --from=frontend-builder /app/dist /app/backend/app/frontend

WORKDIR /app/backend

COPY backend/start.sh /app/backend/start.sh
RUN chmod +x /app/backend/start.sh

CMD ["./start.sh"]