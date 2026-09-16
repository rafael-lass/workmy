# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.10.12 AS uv
FROM python:3.12-slim AS builder

WORKDIR /app
COPY --from=uv /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ─── Stage 2: Imagem final ───────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

COPY --from=uv /uv /uvx /bin/

# Cria usuário não-root para segurança
RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /app

# Copia o ambiente reproduzível criado pelo uv.
COPY --from=builder /app/.venv /app/.venv

COPY pyproject.toml uv.lock alembic.ini ./
COPY migrations/ ./migrations/

# Copia o código fonte
COPY src/ ./src/

# Define variáveis de ambiente padrão (sobrescritas via docker-compose ou .env)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    PORT=8000

USER appuser
EXPOSE 8000

# Healthcheck: verifica disponibilidade do endpoint /health
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["sh", "-c", "uv run --frozen --no-sync alembic upgrade head && exec uvicorn src.presentation.main:app --host 0.0.0.0 --port 8000 --workers 1"]
