# Lumen Diary — один образ: собранный фронтенд отдаётся бэкендом (FastAPI).
# Сборка: docker build -t lumen-diary .
# Запуск:  docker run -p 8000:8000 -e DATA_DIR=/data -v lumen-data:/data lumen-diary

# ---- 1. Сборка фронтенда ----
FROM node:22-bookworm-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- 2. Бэкенд + статика ----
FROM python:3.11-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_DIR=/data
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
# Бэкенд ищет фронтенд в <корень>/frontend/dist относительно backend/app/main.py.
COPY --from=frontend /app/frontend/dist /app/frontend/dist
RUN mkdir -p /data
EXPOSE 8000
# PORT задаёт хостинг (Render/Railway); по умолчанию 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
