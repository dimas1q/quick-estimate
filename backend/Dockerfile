FROM python:3.11-slim

# Установим системные зависимости для wkhtmltopdf
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./app /app/app
COPY ./requirements.txt /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
