# WorkMy

Gestão simples para profissionais autônomos e pequenos prestadores: clientes, catálogo de serviços, projetos e recebimentos.

## O que o projeto oferece

- Dashboard com valores recebidos, pendências e atrasos.
- Clientes e projetos com acompanhamento de etapas e recorrência mensal.
- Serviços com capa, editor visual, tags reutilizáveis e apresentação comercial em PDF.
- Financeiro com confirmação de recebimentos, cancelamento e estorno.
- Login com sessão em cookies HTTP-only, intermediada pelo BFF.

```text
Navegador → Front React/Nginx → BFF Express → Backend FastAPI → PostgreSQL
```

São quatro camadas, sem RabbitMQ, Redis ou worker de filas. A geração de cobranças é solicitada pelo usuário via HTTP. O PDF é renderizado pelo backend em uma thread da aplicação. As dependências Python são gerenciadas exclusivamente com `uv` e `uv.lock`.

## 1. Instalar os pré-requisitos

Para executar tudo com Docker, você precisa apenas de **Git, Docker e Docker Compose v2**. Não precisa instalar Python, Node.js, PostgreSQL ou uv na máquina: as imagens cuidam disso.

### Windows

1. Instale o Git, se ainda não estiver disponível.
2. Siga a [instalação oficial do Docker Desktop para Windows](https://docs.docker.com/desktop/setup/install/windows-install/), incluindo os requisitos de WSL 2 e virtualização.
3. Abra o Docker Desktop e aguarde o engine iniciar. Use containers Linux.
4. Abra um novo terminal PowerShell e confira:

```powershell
git --version
docker --version
docker compose version
docker info
```

### Linux e macOS

Instale Docker Desktop ou, no Linux, Docker Engine com o plugin Compose. Consulte o [guia oficial de instalação do Compose](https://docs.docker.com/compose/install/). Execute os mesmos comandos de verificação acima.

## 2. Baixar o projeto

```bash
git clone https://github.com/rafael-lass/workmy.git
cd workmy
```

Se o repositório exigir autenticação, use sua conta GitHub autorizada. Execute os próximos comandos **na raiz `workmy`**, onde está `docker-compose.yml`.

## 3. Configurar o ambiente

Na primeira instalação, copie o modelo de configuração. **Não sobrescreva um `.env` já configurado.**

PowerShell:

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

Abra `.env` no editor e configure:

| Variável | Uso |
| --- | --- |
| `POSTGRES_USER` | Usuário do banco, por exemplo `workmy_user`. |
| `POSTGRES_PASSWORD` | Senha do banco. Substitua `change_me` antes da primeira inicialização. |
| `POSTGRES_DB` | Nome do banco, por exemplo `workmy_db`. |
| `POSTGRES_PORT` | Porta local do PostgreSQL; padrão `5432`. Pode usar `5433` se já houver outro banco. |
| `JWT_SECRET_KEY` | Segredo aleatório longo usado para assinar sessões. Não use o texto de exemplo. |
| `LOG_FORMAT` | `json` ou `text`. |
| `CORS_ORIGIN` | Para execução local: `http://localhost:5173`. |
| `NODE_ENV` | Para execução local por HTTP: `development`. |

Você pode gerar um segredo sem instalar Python na máquina:

```bash
docker run --rm python:3.12-slim python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Use a saída como valor de `JWT_SECRET_KEY`. Para a senha do banco, um valor aleatório com letras, números, `_` e `-` evita caracteres especiais que precisariam de escape na URL de conexão. Não versione `.env`; somente `.env.example` deve ir ao GitHub.

As variáveis `POSTGRES_*` inicializam o banco quando o volume é criado. Alterá-las depois **não altera automaticamente** as credenciais do banco existente. Não apague o volume para corrigir credenciais se precisar dos dados.

## 4. Construir e iniciar

```bash
docker compose config --quiet
docker compose up -d --build
```

O primeiro build baixa imagens e dependências; pode levar alguns minutos. O Compose sobe:

| Serviço | Responsabilidade | Acesso |
| --- | --- | --- |
| `frontend` | Build React, CSS e Nginx | `http://localhost:5173` |
| `bff` | Cookies de sessão e proxy HTTP | Interno: `bff:3000` |
| `fastapi` | Regras de negócio e PDF | Interno: `fastapi:8000` |
| `postgres` | Persistência PostgreSQL | Local: porta definida em `POSTGRES_PORT` |

O backend aguarda o banco e aplica `uv run --frozen --no-sync alembic upgrade head` antes de iniciar. Não é necessário criar tabelas manualmente.

## 5. Conferir se está funcionando

```bash
docker compose ps
docker compose logs --tail=100 fastapi bff frontend
```

PostgreSQL, FastAPI e BFF devem aparecer como `healthy`; frontend deve estar `Up`. Se ainda estiver `starting`, aguarde e consulte novamente.

Abra **[WorkMy local](http://localhost:5173)**. No primeiro uso:

1. Clique em **Criar conta** e cadastre seu usuário. Não há conta ou senha padrão.
2. Entre e cadastre um cliente.
3. Em **Serviços**, crie um serviço, formate a descrição e selecione/crie tags.
4. Use **Visualizar** para conferir a descrição e **Exportar PDF** para revisar seus contatos e baixar a apresentação.
5. Cadastre um projeto vinculando cliente e serviço.
6. Se configurar recorrência mensal, use **Financeiro → Gerar cobranças vencidas**. Não existe faturamento automático em segundo plano.

Para verificar a versão do banco:

```bash
docker compose exec -T fastapi uv run --frozen --no-sync alembic current
docker compose exec -T fastapi uv run --frozen --no-sync alembic check
```

## 6. Parar e iniciar novamente

Parar sem apagar containers nem dados:

```bash
docker compose stop
docker compose start
```

Remover containers e rede, **preservando o volume do banco**:

```bash
docker compose down
docker compose up -d
```

**Não use `docker compose down -v` na rotina:** `-v` remove o volume e apaga os dados do PostgreSQL. Rebuilds e migrations não precisam desse comando.

## 7. Atualizar sem perder dados

Antes de atualizar um banco importante, faça backup. Se houver alterações locais no código, revise-as antes do pull.

```bash
git pull --ff-only
docker compose up -d --build
docker compose ps
```

O volume é reutilizado e as novas migrations são aplicadas. A migração de serviços preserva descrições anteriores, capas, projetos e colunas legadas de repositório/ferramentas.

### Backup do banco

Exemplo com os valores padrão de usuário e banco (ajuste se mudou o `.env`):

```bash
docker compose exec -T postgres pg_dump -U workmy_user -d workmy_db -Fc -f /tmp/workmy-backup.dump
docker compose cp postgres:/tmp/workmy-backup.dump ./workmy-backup.dump
```

Mova o arquivo para um local seguro; ele contém dados privados. Não o envie ao GitHub. A restauração deve ser feita em um banco escolhido conscientemente, usando `pg_restore`, após conferir o destino e manter uma cópia do estado atual.

## Problemas comuns

| Problema | O que conferir |
| --- | --- |
| `Cannot connect to the Docker daemon` | Abra o Docker Desktop e aguarde o engine iniciar. |
| Porta `5432` ocupada | Altere `POSTGRES_PORT=5433` no `.env` e execute `docker compose up -d`. A comunicação interna continua na porta 5432. |
| Porta `5173` ocupada | Pare o processo conflitante. Se mudar a porta publicada no Compose, atualize também `CORS_ORIGIN`. |
| Falha de download / `EOF` no Docker Hub | Confira rede, proxy/VPN e disponibilidade do registry; tente `docker compose up -d --build` novamente. |
| Backend `unhealthy` ou reiniciando | Veja `docker compose logs --tail=100 fastapi postgres`; confira credenciais e mensagens da migration. Não remova o volume como primeira tentativa. |
| Login falha em HTTP local | Confira `NODE_ENV=development` e `CORS_ORIGIN=http://localhost:5173`. Cookies seguros de produção exigem HTTPS. |
| Tela antiga ou CSS ausente | Reconstrua com `docker compose up -d --build frontend` e faça uma atualização completa no navegador. O CSS é compilado no build e servido pelo Nginx. |
| Imagem retorna erro 413 | O arquivo deve ter até 5 MiB. Nginx e BFF aceitam corpo JSON de 8 MB para acomodar Base64; reconstrua ambos se estiver usando imagens antigas. |
| PDF retorna 401 | Entre novamente; a exportação exige sessão válida e serviço pertencente ao usuário. |

Para acompanhar logs continuamente:

```bash
docker compose logs -f fastapi bff frontend
```

`Ctrl+C` encerra somente o acompanhamento dos logs; os containers continuam rodando.

## Testes e desenvolvimento fora do Docker

Somente para desenvolvimento local, instale Python 3.12/3.13, uv e Node.js 20.19+.

Backend (por padrão, usa SQLite local quando `DATABASE_URL` não está definida):

```bash
cd backend-fastapi
uv sync --frozen
uv run --frozen alembic upgrade head
uv run --frozen pytest -q
```

Frontend:

```bash
cd frontend
npm ci
npm test
npm run lint
npm run build
```

Os blocos acima partem da raiz do repositório; retorne à raiz antes de trocar de camada. Use `uv add`/`uv remove` para dependências Python e versione `pyproject.toml` junto com `uv.lock`.

O GitHub Actions executa testes, valida migrations, verifica o BFF, compila o frontend e as imagens Docker e testa HTML/CSS servido pelo Nginx. Consulte [o guia do desenvolvedor](docs/DEVELOPER_GUIDE.md) para execução sem Docker.

## Antes de publicar em produção

Este Compose é voltado à execução local/staging. Para produção, configure HTTPS, segredos fortes, `NODE_ENV=production`, origem CORS correta, backups e acesso restrito ao banco. Não exponha a porta do PostgreSQL à internet. Não reutilize credenciais de exemplo.

## Documentação

- [Requisitos funcionais](docs/REQUISITOS_FUNCIONAIS.md)
- [Arquitetura das quatro camadas](docs/ARQUITETURA.md)
- [Guia do desenvolvedor](docs/DEVELOPER_GUIDE.md)
- [Editor, tags, migração e PDF de serviços](docs/SERVICOS.md)
