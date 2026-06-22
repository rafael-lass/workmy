# Comunicação Entre Camadas — WorkMy

```
Frontend ──► BFF ──► FastAPI ──► PostgreSQL
 :5173       :3000    :8000       :5432
                        │
                        └──► RabbitMQ :5672
```

---

## 1. Frontend → BFF

O Frontend faz `fetch('/api/...')` e o Vite redireciona para o BFF na porta 3000.

Os cookies de sessão são enviados automaticamente (`credentials: 'include'`). O Frontend **nunca** envia tokens JWT diretamente.

```ts
// frontend/src/lib/http.ts
const res = await fetch(url, {
  method,
  headers,
  body,
  credentials: 'include', // envia cookies HTTP-Only automaticamente
})
```

```ts
// frontend/vite.config.ts
proxy: {
  '/api': { target: 'http://localhost:3000' }
}
```

---

## 2. BFF → FastAPI

O BFF intercepta rotas de auth (login/register/logout) e guarda os tokens JWT em cookies HTTP-Only.

Para as demais rotas `/api/*`, ele lê o cookie, injeta o header `Authorization: Bearer <token>` e encaminha a requisição ao FastAPI.

Se o access token expirou mas o refresh ainda é válido, o BFF renova automaticamente (Silent Refresh).

```js
// frontend/bff/server.js
req.headers['authorization'] = `Bearer ${accessToken}`;
// encaminha para FastAPI via callFastApi()
```

---

## 3. FastAPI → PostgreSQL

Usa SQLAlchemy assíncrono. A URL de conexão vem da env `DATABASE_URL`.

No Docker, aponta para `postgres:5432` (nome do serviço na rede interna).

```python
# backend-fastapi/src/infrastructure/persistence/session.py
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./db.sqlite3")
engine = create_async_engine(DATABASE_URL)
```

---

## 4. FastAPI → RabbitMQ

Conexão persistente via `aio_pika`. Publica eventos quando recursos são criados/atualizados/deletados.

No Docker, aponta para `rabbitmq:5672`.

```python
# backend-fastapi/src/infrastructure/messaging/rabbitmq_publisher.py
self._amqp_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
await self._exchange.publish(message, routing_key=routing_key)
```

---

## 5. FastAPI → Frontend (Tempo Real)

O backend mantém uma conexão SSE aberta. Quando algo muda, envia um evento. O frontend recebe e atualiza a tela automaticamente.

```ts
// frontend/src/hooks/useRealtime.ts
const source = new EventSource(url, { withCredentials: true })
source.addEventListener('projetos', onMessage)
```

---

## Resumo

| De | Para | Protocolo | Porta | Arquivo |
|---|---|---|---|---|
| Frontend | BFF | HTTP + Cookies | 5173 → 3000 | `frontend/vite.config.ts` |
| BFF | FastAPI | HTTP + Bearer JWT | 3000 → 8000 | `frontend/bff/server.js` |
| FastAPI | PostgreSQL | TCP (asyncpg) | 8000 → 5432 | `backend-fastapi/.../session.py` |
| FastAPI | RabbitMQ | AMQP | 8000 → 5672 | `backend-fastapi/.../rabbitmq_publisher.py` |
| FastAPI | Frontend | SSE | 8000 → 5173 | `backend-fastapi/.../events.py` |
