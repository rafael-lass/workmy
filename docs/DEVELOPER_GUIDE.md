# Guia do desenvolvedor

## Pré-requisitos

- Docker com Compose
- Python 3.12 ou 3.13
- `uv`
- Node.js 20.19+

## Aplicação completa

```bash
docker compose up --build
```

O Nginx publica `http://localhost:5173` e encaminha `/api` ao BFF. O FastAPI espera o PostgreSQL ficar saudável, aplica migrations e inicia com um worker.

## Backend com uv

```bash
cd backend-fastapi
uv sync --frozen
uv run --frozen alembic upgrade head
uv run uvicorn src.presentation.main:app --reload
```

Ao alterar modelos:

```bash
uv run alembic revision --autogenerate -m "descricao"
uv run alembic check
uv lock
```

Use `uv add pacote`, `uv remove pacote` e versione `pyproject.toml` com `uv.lock`. Não mantenha `requirements.txt` paralelo.

## Frontend e BFF

```bash
cd frontend/bff
npm ci
npm run dev

cd ..
npm ci
npm run dev
```

O Vite encaminha `/api` para `http://localhost:3000`.

## Verificações locais

```bash
cd backend-fastapi
uv run --frozen pytest -q
uv run --frozen alembic check

cd ../frontend
npm test
npm run lint
npm run build

cd bff
node --check server.js

cd ../..
docker compose config --quiet
docker compose build
```

O CI executa as mesmas etapas, sobe o stack e confirma que `/login`, `/dashboard` e o CSS compilado são servidos pelo Nginx com MIME correto.

## Reset local do banco

O comando abaixo remove definitivamente o volume PostgreSQL do projeto:

```bash
docker compose down -v
docker compose up --build
```

Use esse reset somente em ambientes descartáveis e com autorização explícita para perder os dados. Atualizações normais, incluindo o editor e as tags de serviços, preservam os dados por migrations. Em produção, nunca remova o volume; mantenha backup e aplique apenas migrations. Veja o passo a passo de instalação no [README principal](../README.md).
