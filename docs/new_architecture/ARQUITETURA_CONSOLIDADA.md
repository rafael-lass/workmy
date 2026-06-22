# 🏛️ WorkMy — Arquitetura Consolidada

> Documento único que reúne a **arquitetura geral**, os **diagramas de use cases** e o mapa de **como tudo se conecta** na plataforma WorkMy.
> Os diagramas estão em **Mermaid.js** e renderizam direto no GitHub, VS Code (extensão Mermaid) ou qualquer visualizador Markdown compatível.
>
> Companheiro deste documento: **[`BOOK_CONCEITOS.md`](./BOOK_CONCEITOS.md)** — explica cada conceito do código e como usá-lo.

---

## 1. O que é o WorkMy

WorkMy é uma plataforma **fullstack** para gestão de atividades freelance: clientes, serviços, projetos/contratos, controle financeiro de faturamento real acumulado e geração de cobranças recorrentes idempotentes, **isolada por usuário (multitenant lógico)**.

O sistema é um **monorepo desacoplado** composto por quatro processos independentes que se comunicam por rede:

| Processo | Tecnologia | Papel | Porta padrão |
|----------|-----------|-------|--------------|
| **SPA** | React 19 + Vite + TypeScript | Interface do usuário (browser) | 5173 |
| **BFF** | Node.js + Express | Gateway de segurança: cookies HTTP-Only, silent refresh, proxy | 3000 |
| **Core API** | Python + FastAPI + SQLAlchemy async | Regras de negócio (Arquitetura Hexagonal) | 8000 |
| **Persistência / Mensageria** | PostgreSQL 15 + RabbitMQ 3 | Dados ACID + eventos assíncronos | 5432 / 5672 |

---

## 2. Arquitetura Principal (visão multicamadas)

Cada caixa é um processo separado. A regra de ouro: **o browser nunca fala direto com o FastAPI nem vê o JWT** — tudo passa pelo BFF, que guarda os tokens em cookies HTTP-Only.

```mermaid
flowchart TB
    subgraph Browser["🌐 Browser do Usuário"]
        SPA["React SPA (Vite + TS)<br/>Páginas, Hooks, Cache LocalStorage"]
    end

    subgraph Edge["🛡️ Camada de Borda (Node.js)"]
        BFF["BFF — Express Gateway<br/>• Cookies HTTP-Only (access/refresh)<br/>• Silent Refresh automático<br/>• Injeção de Bearer JWT<br/>• Proxy /api/* e SSE"]
    end

    subgraph CoreSvc["⚙️ Core Service (Python / FastAPI)"]
        direction TB
        PRES["Presentation<br/>Routers REST + Middleware Auth + DTOs"]
        APP["Application<br/>Use Cases + Ports (interfaces)"]
        DOM["Domain<br/>Entities + Regras + Exceptions"]
        INFRA["Infrastructure<br/>Repositories + JWT + RabbitMQ Publisher"]
        PRES --> APP --> DOM
        APP -. depende de interfaces .-> INFRA
    end

    subgraph Data["💾 Dados & Eventos"]
        PG[("PostgreSQL 15<br/>Transações ACID")]
        MQ{{"RabbitMQ 3<br/>exchange 'workmy_events' (topic)"}}
    end

    SPA -- "fetch credentials:include<br/>(cookies)" --> BFF
    SPA -- "EventSource SSE" --> BFF
    BFF -- "HTTP + Authorization: Bearer" --> PRES
    BFF -- "proxy stream SSE" --> PRES
    INFRA -- "SQLAlchemy async / asyncpg" --> PG
    INFRA -- "aio-pika (publish)" --> MQ
    PRES -- "GET /events/stream (SSE)" --> SPA
```

### Por que essa separação?

- **SPA isolada:** rápida, renderiza no browser, mantém cache local para reduzir latência.
- **BFF como guardião do token:** o JWT vive em cookie `HttpOnly` + `Secure` + `SameSite`, inacessível a JavaScript — mitiga XSS/roubo de token. O BFF também faz o *silent refresh* quando o access token expira.
- **Core API stateless:** valida o `Bearer` em cada request, aplica regras de negócio e devolve JSON. Não guarda sessão.
- **Postgres + RabbitMQ:** dados consistentes (ACID) e eventos assíncronos para invalidação de cache em tempo real (SSE).

---

## 3. Arquitetura Hexagonal do Core (Clean Architecture)

O backend FastAPI segue **Ports & Adapters**. A direção das dependências aponta sempre para dentro: a camada de fora conhece a de dentro, **nunca o contrário**. O `Domain` não importa nada de framework.

```mermaid
flowchart LR
    subgraph EXT["🔌 Mundo Externo"]
        HTTP["HTTP / REST"]
        DBX[("PostgreSQL")]
        RMQ{{"RabbitMQ"}}
    end

    subgraph PRESENTATION["Presentation (Adapters de Entrada)"]
        ROUTERS["rest/*.py<br/>auth, clientes, servicos,<br/>projetos, pagamentos,<br/>dashboard, faturamento, events"]
        DEPS["dependencies.py<br/>(Injeção de Dependências)"]
        MW["middleware/auth.py<br/>(valida JWT)"]
    end

    subgraph APPLICATION["Application"]
        UC["usecases/*.py<br/>CriarProjeto, FaturarRecorrencias,<br/>AuthUseCases, Crud*..."]
        PORTS["ports/outbound/*.py<br/>I*Repository, IEventPublisher,<br/>ITokenService, IPasswordHasher"]
        DTO["dto/views.py<br/>(read models)"]
    end

    subgraph DOMAIN["Domain (Núcleo Puro)"]
        ENT["entities/*.py<br/>Projeto, Cliente, Servico,<br/>Pagamento, Usuario"]
        EXC["exceptions/business_exceptions.py"]
    end

    subgraph INFRASTRUCTURE["Infrastructure (Adapters de Saída)"]
        REPOS["persistence/repositories/*.py<br/>Postgres*Repo (implementam Ports)"]
        MODELS["persistence/models.py<br/>(SQLAlchemy ORM)"]
        SEC["security/*.py<br/>JWT + Bcrypt (implementam Ports)"]
        PUB["messaging/rabbitmq_publisher.py<br/>(implementa IEventPublisher)"]
    end

    HTTP --> ROUTERS
    ROUTERS --> MW
    ROUTERS --> DEPS
    DEPS -. injeta .-> UC
    UC --> ENT
    UC --> EXC
    UC -- "chama via interface" --> PORTS
    REPOS -. implementa .-> PORTS
    SEC -. implementa .-> PORTS
    PUB -. implementa .-> PORTS
    REPOS --> MODELS --> DBX
    PUB --> RMQ
```

**Leitura do diagrama:** o `Use Case` depende apenas de **interfaces** (`Ports`). Quem decide qual implementação concreta entra é o `dependencies.py` (composição). Trocar Postgres por outro banco, ou RabbitMQ por Kafka, não toca no domínio nem nos use cases.

---

## 4. Modelo de Dados (ER)

Todas as entidades de negócio pertencem a um `usuario` (isolamento multitenant). Deleções são **soft delete** (`deletado_em`).

```mermaid
erDiagram
    USUARIOS ||--o{ CLIENTES : possui
    USUARIOS ||--o{ SERVICOS : possui
    USUARIOS ||--o{ PROJETOS : possui
    CLIENTES ||--o{ PROJETOS : contratante
    SERVICOS ||--o{ PROJETOS : contratado
    PROJETOS ||--o{ PAGAMENTOS : gera

    USUARIOS {
        int id PK
        string username UK
        string email UK
        string telefone
        string password_hash
    }
    CLIENTES {
        int id PK
        int usuario_id FK
        string nome
        string empresa
        string email
        string telefone
        datetime criado_em
        datetime deletado_em
    }
    SERVICOS {
        int id PK
        int usuario_id FK
        string nome
        string descricao
        string tags
        string ferramentas
        string github_repo
        blob imagem_bytes
        datetime deletado_em
    }
    PROJETOS {
        int id PK
        int usuario_id FK
        int cliente_id FK
        int servico_id FK
        string status
        int progresso
        decimal valor
        bool mensalista
        decimal valor_mensal
        int dia_vencimento
        date recorrencia_inicio
        string tipo_recorrencia
        bool recorrencia_ativa
        datetime deletado_em
    }
    PAGAMENTOS {
        int id PK
        int projeto_id FK
        decimal valor
        string tipo_pagamento
        date data
        string referencia_mes
        bool gerado_automaticamente
        blob comprovante_bytes
        datetime deletado_em
    }
```

> 🔑 **Regra de integridade chave:** `PAGAMENTOS` tem `UniqueConstraint(projeto_id, referencia_mes)`. É isso que torna a recorrência mensal **idempotente** — impossível faturar duas vezes o mesmo mês de um projeto.

### Máquina de estados do Projeto

O `status` de um projeto só transita por caminhos permitidos (`STATUS_TRANSITIONS` em `domain/entities/projeto.py`):

```mermaid
stateDiagram-v2
    [*] --> DISCOVERY
    DISCOVERY --> IN_PROGRESS
    DISCOVERY --> ARCHIVED
    IN_PROGRESS --> REVIEW
    IN_PROGRESS --> ARCHIVED
    REVIEW --> IN_PROGRESS
    REVIEW --> COMPLETED
    REVIEW --> ARCHIVED
    COMPLETED --> ARCHIVED
    ARCHIVED --> [*]
```

---

## 5. Diagramas de Use Cases

### 5.1 Autenticação — Login com cookies HTTP-Only

```mermaid
sequenceDiagram
    actor U as Usuário
    participant SPA as React SPA
    participant BFF as BFF (Express)
    participant API as FastAPI
    participant UC as AuthUseCases
    participant DB as PostgreSQL

    U->>SPA: preenche login + senha
    SPA->>BFF: POST /api/auth/login (credentials:include)
    BFF->>API: POST /api/auth/login {email, password}
    API->>UC: login(email, password)
    UC->>DB: get_by_email / get_by_username
    DB-->>UC: UsuarioEntity
    UC->>UC: password_hasher.verify(senha, hash)
    UC-->>API: usuario + access + refresh (JWT)
    API-->>BFF: 200 {access, refresh, user}
    BFF->>BFF: Set-Cookie HttpOnly (workmy_access, workmy_refresh)
    BFF-->>SPA: 200 {user}  (sem tokens!)
    SPA->>SPA: persistUser() + clearApiCache()
    SPA-->>U: redireciona /dashboard
```

### 5.2 Silent Refresh — renovação transparente do token

Quando o access token (15 min) expira mas o refresh (7 dias) ainda vale, o BFF renova **sem o usuário perceber**.

```mermaid
sequenceDiagram
    participant SPA as React SPA
    participant BFF as BFF (Express)
    participant API as FastAPI

    SPA->>BFF: GET /api/projetos (cookie access expirado)
    BFF->>BFF: access ausente/expirado, refresh válido?
    BFF->>API: POST /api/auth/refresh {refresh}
    API-->>BFF: 200 {access novo}
    BFF->>BFF: Set-Cookie workmy_access (novo)
    BFF->>API: GET /api/projetos (Authorization: Bearer novo)
    API-->>BFF: 200 dados
    BFF-->>SPA: 200 dados
    Note over SPA,BFF: Se refresh inválido → 401 + cookies limpos → re-login
```

### 5.3 Criar Projeto — regras de negócio + evento assíncrono

```mermaid
sequenceDiagram
    participant SPA
    participant BFF
    participant R as Router projetos
    participant UC as CriarProjetoUseCase
    participant CR as ClienteRepo
    participant SR as ServicoRepo
    participant PR as ProjetoRepo
    participant EV as RabbitMQ Publisher
    participant DB as PostgreSQL

    SPA->>BFF: POST /api/projetos {cliente_id, servico_id, ...}
    BFF->>R: POST /api/projetos (Bearer JWT)
    R->>R: get_current_user_id (valida JWT)
    R->>UC: execute(usuario_id, cliente_id, servico_id, ...)
    UC->>CR: exists_by_id(cliente_id, usuario_id)
    UC->>SR: exists_by_id(servico_id, usuario_id)
    UC->>PR: exists_active_contract(cliente, servico)
    alt contrato ativo já existe
        UC-->>R: ColisaoContratoException
        R-->>BFF: 400 detalhe
    else ok
        UC->>UC: ProjetoEntity().validate()
        UC->>PR: save(projeto)
        PR->>DB: INSERT
        UC->>EV: publish('projetos','created')
        EV-->>SPA: (SSE) invalida cache
        UC-->>R: ProjetoEntity
        R-->>BFF: 201 ProjetoOut
    end
```

### 5.4 Faturamento Recorrente Idempotente

Executado sob demanda; gera **uma única** mensalidade por mês por projeto.

```mermaid
flowchart TD
    START([POST /api/faturamento/recorrencias]) --> LIST["projeto_repo.list_recorrentes_ativos(usuario)"]
    LIST --> LOOP{Para cada projeto recorrente}
    LOOP --> D{hoje.day >= dia_vencimento?}
    D -- não --> LOOP
    D -- sim --> INI{recorrencia_inicio já chegou?}
    INI -- não --> LOOP
    INI -- sim --> EXISTS{"Já existe pagamento<br/>p/ referencia_mes?"}
    EXISTS -->|"sim (idempotência)"| LOOP
    EXISTS -->|não| VAL{valor_mensal ou valor válido?}
    VAL -- não --> LOOP
    VAL -- sim --> SAVE["cria PagamentoEntity MENSAL<br/>gerado_automaticamente=True<br/>pagamento_repo.save()"]
    SAVE --> PUB["event_publisher.publish('pagamentos','created')"]
    PUB --> LOOP
    LOOP --> END([retorna pagamentos gerados])
```

### 5.5 Tempo Real (SSE) + Invalidação de Cache

```mermaid
sequenceDiagram
    participant SPA as SPA (useRealtime)
    participant BFF
    participant API as FastAPI /events/stream
    participant UC as Use Case (mutação)

    SPA->>BFF: EventSource /api/events/stream
    BFF->>API: proxy stream (Bearer)
    API-->>SPA: event: connected
    loop heartbeat 30s
        API-->>SPA: : heartbeat
    end
    Note over UC: alguém cria/edita um recurso
    UC->>API: notify_user(usuario_id, resource, action)
    API-->>SPA: event: projetos {resource, action}
    SPA->>SPA: handleRealtimeEvent → invalida escopo no cache
    SPA->>BFF: re-fetch GET (forceRefresh) do recurso afetado
```

---

## 6. Como tudo se conecta (resumo do fluxo de uma requisição)

```mermaid
flowchart LR
    A["Componente React<br/>(ex: ProjetosPage)"] --> B["useResourceQuery / useApi"]
    B --> C{"Cache LocalStorage<br/>válido?"}
    C -- sim --> A
    C -- não --> D["http() fetch<br/>credentials:include"]
    D --> E["BFF: injeta Bearer<br/>do cookie HttpOnly"]
    E --> F["FastAPI Router<br/>+ middleware JWT"]
    F --> G["Use Case<br/>(Application)"]
    G --> H["Entity.validate()<br/>(Domain)"]
    G --> I["Repository<br/>(Infrastructure) → Postgres"]
    G --> J["Publisher → RabbitMQ"]
    I --> F
    F --> E --> D
    D --> K["writeCache()"]
    K --> A
    J -. SSE .-> L["useRealtime → invalida cache"]
    L --> B
```

### Mapa de tecnologias por responsabilidade

| Responsabilidade | Tecnologia | Onde no código |
|---|---|---|
| UI / Roteamento SPA | React 19, React Router 7, Vite | `frontend/src/App.tsx`, `pages/`, `components/` |
| Cache cliente + tempo real | LocalStorage + EventSource (SSE) | `frontend/src/shared/lib/cache.ts`, `hooks/useRealtime.ts` |
| Segurança de sessão | Cookies HTTP-Only + silent refresh | `frontend/bff/server.js` |
| API REST async | FastAPI + Pydantic | `backend-fastapi/src/presentation/` |
| Regras de negócio | Use Cases + Domain Entities | `backend-fastapi/src/application/`, `domain/` |
| Persistência | SQLAlchemy 2 async + asyncpg | `backend-fastapi/src/infrastructure/persistence/` |
| Autenticação | JWT (python-jose) + bcrypt | `backend-fastapi/src/infrastructure/security/` |
| Mensageria | RabbitMQ + aio-pika | `backend-fastapi/src/infrastructure/messaging/` |
| Orquestração local | Docker Compose | `docker-compose.yml` |

---

## 7. Decisões arquiteturais de destaque

1. **BFF guarda o token, não o browser** — o JWT nunca chega ao JavaScript do SPA; vive em cookie `HttpOnly`. Mitiga XSS.
2. **Stateless no core** — o FastAPI não tem sessão; cada request carrega o `Bearer`. Escala horizontalmente.
3. **Idempotência por constraint** — `UniqueConstraint(projeto_id, referencia_mes)` impede cobrança duplicada no nível do banco.
4. **Soft delete em tudo** — `deletado_em` preserva histórico e permite recontratação após exclusão lógica.
5. **Publisher resiliente** — RabbitMQ offline não derruba a API; o evento é descartado com `warning` (`rabbitmq_publisher.py`).
6. **Cache write-through com invalidação por SSE** — leitura instantânea + consistência quase em tempo real.
7. **Dashboard O(1)** — agregações feitas via `func.sum`/`group_by` no Postgres, não em loop Python (`postgres_dashboard_query.py`).

---

*Detalhamento conceitual de cada item acima → veja **[`BOOK_CONCEITOS.md`](./BOOK_CONCEITOS.md)**.*
