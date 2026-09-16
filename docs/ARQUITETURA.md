# Arquitetura

## Visão implantável

```text
React SPA/Nginx ── HTTP + cookies ──► BFF Express ── Bearer JWT ──► FastAPI ──► PostgreSQL
```

Há somente quatro responsabilidades: interface, sessão/proxy, regras/API e persistência. Toda operação remota é explícita e síncrona do ponto de vista do usuário. `async`/`await` é usado no FastAPI e nos adapters SQLAlchemy apenas para I/O.

## Backend

O backend mantém dependências voltadas para dentro:

```text
presentation → application → domain
      │              │
      └── composition root ──► infrastructure
```

- `domain`: entidades, estados e invariantes sem FastAPI/SQLAlchemy.
- `application`: casos de uso e portas abstratas.
- `infrastructure`: repositórios SQLAlchemy e segurança.
- `presentation`: schemas e tradução HTTP.
- `dependencies.py`: composition root.

Alembic é a única fonte de evolução de schema. A aplicação não executa `create_all` no startup.

## Frontend

O frontend é organizado por recurso: `clientes`, `servicos`, `projetos` e `financeiro`. Páginas compõem esses recursos e carregam os próprios dados; não existe store global, cache privado persistente ou canal realtime.

Formulários canônicos são diálogos compartilhados. A base de UI contém botão, campo, alerta, badge, confirmação, toast, skeleton e estado vazio. Ícones são SVGs empacotados no bundle; não há dependência visual externa em runtime.

## BFF

O BFF possui uma função: delimitar a sessão web. Ele converte as respostas de login em cookies HTTP-only, renova o access token e encaminha as rotas `/api`. Não contém regras de projeto ou financeiras.

## Consistência financeira

A máquina de estados vive no domínio. A referência mensal possui unicidade `(projeto_id, referencia_mes)` no banco; o repositório também trata colisões concorrentes. Totais filtram `status=PAGO`, fazendo cancelamentos e estornos desaparecerem naturalmente do realizado.
