# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS node
WORKDIR /bff
COPY frontend/bff/package*.json ./
RUN npm ci --omit=dev --ignore-scripts

FROM ghcr.io/astral-sh/uv:0.10.12 AS uv
FROM python:3.12-slim-bookworm AS python-build
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app/backend
COPY backend-fastapi/pyproject.toml backend-fastapi/uv.lock ./
ENV UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/app/.venv
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 ca-certificates fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* && useradd --create-home appuser
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /bff/node_modules /app/bff/node_modules
COPY --from=python-build /app/.venv /app/.venv
COPY frontend/bff/server.js /app/bff/server.js
COPY backend-fastapi/src /app/backend/src
COPY backend-fastapi/migrations /app/backend/migrations
COPY backend-fastapi/alembic.ini /app/backend/alembic.ini
COPY deploy/render/supervise.py /app/deploy/supervise.py
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app/backend \
    PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=cloud NODE_ENV=production PORT=10000 FASTAPI_URL=http://127.0.0.1:8000
WORKDIR /app/backend
USER appuser
EXPOSE 10000
CMD ["python", "/app/deploy/supervise.py"]
