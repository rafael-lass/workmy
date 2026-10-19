# WorkMy na nuvem: Vercel + Render + Supabase

Este roteiro publica uma demonstração com dados pequenos. Os servidores e o CI/CD ficam na nuvem; sua máquina só é necessária para configurar o repositório. Use contas pessoais e planos Free/Hobby. As franquias e a disponibilidade dependem dos provedores; confira os painéis antes de escolher qualquer recurso pago.

## 1. O que conversa com o quê

```text
Navegador
  └─ HTTPS https://SEU-PROJETO.vercel.app
       ├─ React estático
       └─ /api/* → HTTPS https://SEU-BACKEND.onrender.com/api/*
                       └─ BFF, porta $PORT (10000)
                            └─ HTTP 127.0.0.1:8000, FastAPI
                                 └─ PostgreSQL com TLS e certificado verificado
                                      Session Pooler Supabase, porta 5432
```

O navegador usa apenas a origem da Vercel. Não configure o React para chamar diretamente o domínio do Render: cookies `SameSite=Strict` não funcionam nessa combinação entre sites diferentes. O proxy mantém os cookies `HttpOnly`, `Secure`, `Path=/`, sem `Domain`, associados ao domínio da Vercel. Nenhum JWT é devolvido no JSON do login.

Vercel e Render emitem os certificados HTTPS dos próprios subdomínios. Não é necessário comprar domínio, instalar Nginx no Render ou abrir portas manualmente. O TLS termina na borda do Render; dentro do container o BFF usa HTTP local. FastAPI não escuta na interface pública.

O Compose normal continua sendo o ambiente local. O Dockerfile específico da nuvem reúne BFF e FastAPI em um container, aplica migrations e supervisiona ambos. O banco é externo; os arquivos temporários do Render não armazenam dados permanentes. Capas e comprovantes continuam no PostgreSQL.

## 2. Preparação e ordem de configuração

Tenha Git, Node 22+ e acesso ao repositório no GitHub. Docker e Python/uv são opcionais para configurar a hospedagem, mas necessários para reproduzir todos os testes localmente. Em uma nova instalação do Node ou Docker, abra um terminal novo para atualizar o PATH.

As ações iniciais ainda não publicam automaticamente: `CLOUD_DEPLOY_ENABLED` começa ausente. Crie os recursos e preencha os campos antes de habilitá-la.

### Supabase: criar o banco

1. Crie um projeto **Free** exclusivo para o WorkMy. Sugestão de região: US East / North Virginia, próxima ao Render Virginia.
2. Defina e guarde a senha do banco em um gerenciador de senhas.
3. Desative a **Data API** no painel do projeto, em Integrations/Data API ou Settings/Data API. O WorkMy usa SQLAlchemy diretamente; as APIs REST/GraphQL do Supabase não devem oferecer outro acesso às tabelas. A autenticação continua sendo a do WorkMy.
4. Em **Connect → Session pooler**, copie host, usuário `postgres.<project-ref>`, banco e porta **5432**.
5. Nas configurações de conexão/SSL do banco, baixe o certificado CA fornecido pelo Supabase. Abra o PEM em um editor: ele deve conter `-----BEGIN CERTIFICATE-----` e `-----END CERTIFICATE-----` em linhas próprias.
6. Não crie tabelas pelo SQL Editor. O primeiro startup aplica o Alembic.

Use o pooler em modo **sessão**. A conexão direta padrão pode depender de IPv6; Render usa IPv4. O pooler transacional, porta 6543, tem comportamento diferente para prepared statements e não é usado aqui.

Para montar as URLs com a senha escapada, execute na raiz, se tiver Python:

```powershell
python deploy/database-url.py
```

Alternativa com Docker, sem Python local:

```powershell
docker run --rm -it --mount "type=bind,source=$PWD/deploy,target=/scripts,readonly" python:3.12-slim python /scripts/database-url.py
```

O programa pede a senha sem colocá-la no histórico e mostra duas URLs. Copie a primeira para o Render e a segunda para o secret de backup. A senha aparecerá codificada na saída: não compartilhe o terminal ou faça screenshots desse resultado.

```text
DATABASE_URL:
postgresql+asyncpg://postgres.PROJECT_REF:SENHA_ESCAPADA@POOLER_HOST:5432/postgres

BACKUP_DATABASE_URL:
postgresql://postgres.PROJECT_REF:SENHA_ESCAPADA@POOLER_HOST:5432/postgres
```

Não acrescente `sslmode` à URL asyncpg. O código fornece um `SSLContext` com o CA, verificação de hostname e certificado, tanto na aplicação quanto no Alembic. O backup usa libpq com `sslmode=verify-full`.

### Vercel: reservar o endereço do frontend

1. Importe o repositório em **Add New → Project**, com o plano pessoal Hobby.
2. Defina **Root Directory = `frontend`**, framework **Vite**, build `npm run build`, output `dist`, instalação `npm ci` e Node 22.
3. Cadastre em **Environment Variables → Production**:

   | Nome | Valor |
   |---|---|
   | `VITE_API_BASE_URL` | `/api` |
   | `VITE_CLOUD_DEMO` | `true` |

4. Anote a URL de produção estável, por exemplo `https://workmy-demo.vercel.app`. Use-a sem barra final. As URLs aleatórias de deployments/previews não são a URL canônica.
5. O arquivo `frontend/vercel.json` desativa deploys automáticos pela integração Git. Se a importação solicitar uma primeira publicação, ela serve apenas para provisionar/reservar o endereço: o login só estará pronto após configurar o Render e executar o pipeline.
6. Gere um token em **Account Settings → Tokens**, com o menor escopo disponível para seu projeto/conta. Anote **Project ID**, nas configurações do projeto, e **Organization/Team ID**, nas configurações da conta/workspace.

Alternativa para obter IDs: na raiz do repositório, após instalar `deploy/ci` com `npm ci`, execute `node deploy/ci/node_modules/vercel/dist/vc.js link`. Selecione o projeto que já existe; veja os IDs no arquivo `.vercel/project.json`. O diretório `.vercel` é ignorado pelo Git. Os comandos do pipeline são executados **na raiz do repositório**, preservando o Root Directory `frontend` configurado no painel.

Nenhum `DATABASE_URL`, senha ou JWT secret deve existir em variáveis `VITE_*`: elas entram no JavaScript público.

### Render: criar o container do backend

1. A implementação deve estar no seu repositório remoto para o Render enxergar o Dockerfile. Faça o commit/push após revisar as alterações locais.
2. Crie **New → Web Service → Git Repository**, selecionando esse repositório e a branch `main`.
3. Escolha **Docker**, região **Virginia** e instância **Free**.
4. Deixe o Root Directory vazio: o contexto é a raiz do repositório. Dockerfile Path: `deploy/render/Dockerfile`; Docker Build Context: `.`. Deixe Docker Command vazio para usar o `CMD` da imagem.
5. Configure Health Check Path: `/api/health/ready`.
6. Desative **Auto-Deploy**. O GitHub Actions será o único coordenador de publicação.
7. Cadastre as variáveis abaixo. Há uma referência em `deploy/cloud.env.example`.

   | Nome | Valor |
   |---|---|
   | `APP_ENV` | `cloud` |
   | `NODE_ENV` | `production` |
   | `PORT` | `10000` |
   | `FASTAPI_URL` | `http://127.0.0.1:8000` |
   | `APP_PUBLIC_URL` | URL HTTPS estável da Vercel, sem barra final |
   | `CORS_ORIGIN` | Exatamente a mesma URL |
   | `CORS_ORIGINS` | Exatamente a mesma URL |
   | `DATABASE_URL` | URL asyncpg criada acima |
   | `DATABASE_CA_CERT` | Conteúdo inteiro do PEM, com as quebras de linha |
   | `JWT_SECRET_KEY` | Segredo aleatório forte e permanente |
   | `LOG_FORMAT` | `json` |
   | `EXCEL_EXPORT_MODE` | `sequential` |
   | `EXCEL_EXPORT_MAX_ROWS` | `2000` |
   | `EXCEL_EXPORT_MAX_CONCURRENT` | `1` |
   | `EXCEL_PROXY_TIMEOUT_MS` | `90000` |

8. Para gerar o JWT secret: `node -e "console.log(require('crypto').randomBytes(48).toString('base64url'))"`. Não gere outro a cada deploy; trocar o segredo invalida as sessões.
9. Anote o domínio `https://SEU-BACKEND.onrender.com`, sem barra final, e o **Service ID**, que começa com `srv-` e aparece na URL/configurações do serviço.
10. Em **Account Settings → API Keys**, crie uma chave para o pipeline.

O primeiro provisionamento aplica migrations. Se falhar, confira os logs antes de repetir. Não use SQLite, volume/disco persistente ou um segundo serviço gratuito para o BFF. O Render Free não recebe tráfego pela rede privada e dois serviços acrescentariam cold starts e disputa pela franquia de horas.

### GitHub: secrets, variáveis e primeira publicação

Crie o Environment **production** em Settings → Environments. Cadastre secrets nele ou em Settings → Secrets and variables → Actions. As **Variables** da tabela devem ser variáveis do **repositório**, em Settings → Secrets and variables → Actions → Variables, não variáveis do Environment: `CLOUD_DEPLOY_ENABLED` é avaliada antes de o job acessar o Environment. Todos os nomes abaixo são exatos.

| Tipo | Nome | Conteúdo |
|---|---|---|
| Secret | `RENDER_API_KEY` | Chave da API Render |
| Secret | `VERCEL_TOKEN` | Token Vercel |
| Secret | `VERCEL_ORG_ID` | Organization/Team ID Vercel |
| Secret | `VERCEL_PROJECT_ID` | Project ID Vercel |
| Variable | `RENDER_SERVICE_ID` | `srv-...` |
| Variable | `RENDER_URL` | Origem HTTPS do Render, sem barra final |
| Variable | `APP_URL` | Origem HTTPS estável da Vercel, sem barra final |
| Variable | `CLOUD_DEPLOY_ENABLED` | `true`, somente após preencher tudo |
| Secret | `SMOKE_USERNAME` | Conta WorkMy exclusiva para checks, após o primeiro deploy |
| Secret | `SMOKE_PASSWORD` | Senha dessa conta |

O pipeline gera o rewrite a partir de `RENDER_URL` antes do build. O placeholder `.invalid` versionado é deliberado: não é um backend real. Para conferir/preencher o rewrite localmente, use:

```powershell
node deploy/configure-vercel.mjs https://SEU-BACKEND.onrender.com
```

O script mantém `/api` no destino e posiciona essa regra antes do fallback de páginas. Não use uma URL `http://`, `/api` no fim da variável `RENDER_URL`, ou uma URL com credenciais.

Em **Actions → CI → Run workflow**, selecione `main`. O pipeline executa os testes antes de usar credenciais de produção. No primeiro deploy, o check autenticado é explicitamente ignorado se ambos os secrets de smoke estiverem ausentes; os checks públicos de HTTPS, proxy e SHA continuam obrigatórios.

Depois abra a URL da Vercel, crie sua conta de demonstração e uma conta separada para smoke. Cadastre os dois secrets de smoke e execute CI novamente para comprovar login/refresh/logout no domínio real.

Ative regras de proteção/rulesets da `main` conforme o plano GitHub: exigir PR e os checks de backend, bff, frontend, images, postgres-migrations (15/17) e cloud-e2e. Se escolher aprovação manual no Environment production, o job aguardará sua aprovação; isso é opcional e não é exigido pelo workflow.

## 3. Como a entrega funciona depois

```text
PR → testes Python/UI/BFF + migrations + Docker + navegador HTTPS
main → mesmos checks → prepara frontend → Render no SHA exato
     → aguarda live + ready + SHA → publica frontend preparado
     → verifica domínio Vercel e sessão autenticada
```

Há uma única publicação em andamento. Pushes de PRs não recebem secrets. O deploy usa o SHA aprovado, não apenas “o último commit da branch”. Builds e dependências usam lockfiles; a Vercel CLI e Playwright também estão fixados em `deploy/ci/package-lock.json`.

Se o Render falhar, o frontend não é publicado. Se o frontend falhar depois do backend, a versão anterior do frontend continuará ativa: por isso mudanças de API e migrations precisam ser compatíveis com a versão anterior. Use migrations aditivas e separe remoções de colunas de sua primeira alteração de código. Um timeout no POST de deploy exige consultar o painel: o workflow não repete automaticamente essa operação.

O health check consulta o banco e informa `status` e `commit`; não mostra hostname ou erros de credencial. O SHA é fornecido por `RENDER_GIT_COMMIT`, ou por `APP_COMMIT_SHA` nos testes. Todas as respostas `/api` usam `no-store`, e o rewrite desativa explicitamente o cache com `x-vercel-enable-rewrite-caching: 0`. Isso cobre o comportamento de cache de origens externas adotado pela Vercel em abril de 2026.

### Cold starts e exportação

- Render Free suspende após inatividade. A interface aguarda prontidão por até 100 segundos e permite tentar novamente. Somente probes GET são repetidos; não há repetição automática de pagamentos após timeout.
- Supabase Free também pode pausar por inatividade. Se isso acontecer, restaure pelo painel antes da demonstração.
- A exportação cloud é sequencial, com uma geração por vez e até 2.000 registros **somados** entre pagamentos, clientes, serviços e projetos. O limite é contado no mesmo snapshot, antes de ler todas as linhas.
- `422` significa que é preciso reduzir o período; `429`, aguardar outra exportação. A capacidade só é liberada quando a renderização terminar, mesmo se o cliente desconectar.
- O BFF espera até 90 segundos por exportação; o proxy externo da Vercel tem limite de 120 segundos. A carga acadêmica de 200 mil pagamentos continua sendo um benchmark local.
- Capas/comprovantes ocupam os 500 MB de banco. Uma capa de 5 MiB enviada em Base64 ocupa quase 7 MB no request; mantenha os limites alinhados e use imagens pequenas na demonstração.

## 4. Backup criptografado e recuperação

Supabase Free não inclui backup automático. O workflow manual **Backup criptografado** salva somente o schema `public`, onde ficam as tabelas WorkMy. Os schemas internos do Supabase não entram no dump.

Cadastre no Environment production:

| Secret | Conteúdo |
|---|---|
| `BACKUP_DATABASE_URL` | URL libpq, prefixo `postgresql://`, Session Pooler porta 5432 |
| `DATABASE_CA_CERT` | O mesmo CA PEM usado no Render |
| `BACKUP_PASSPHRASE` | Segredo aleatório de pelo menos 32 caracteres, guardado também fora do GitHub |

Execute **Actions → Backup criptografado → Run workflow → main** antes de mudar schema e antes de apagar recursos. O script identifica a versão do servidor e usa `pg_dump` da mesma versão. Credenciais são passadas por ambiente; o dump em texto puro existe apenas em diretório temporário no runner. Somente o arquivo `.dump.gpg` é enviado como artifact, com retenção de sete dias. Faça download para uma cópia durável. Artifacts de repositórios públicos podem ser acessíveis: a criptografia e a guarda externa da senha são necessárias.

Para restaurar:

1. Desabilite temporariamente `CLOUD_DEPLOY_ENABLED`, para evitar publicação concorrente.
2. Crie **outro projeto Supabase vazio**, desative a Data API e obtenha sua conexão Session Pooler e CA. Não use a URL do projeto com dados existentes.
3. Em um computador com GnuPG, descriptografe: `gpg --output workmy-restore.dump --decrypt workmy-AAAA.dump.gpg`. O programa solicita a senha.
4. Use uma imagem `postgres:MAJOR-bookworm`, com a mesma versão principal do servidor de destino. Passe `PGHOST`, `PGPORT=5432`, `PGUSER`, `PGPASSWORD`, `PGDATABASE=postgres`, `PGSSLMODE=verify-full` e `PGSSLROOTCERT=/restore/ca.crt` em um arquivo de ambiente local fora do Git.
5. Coloque dump e CA em uma pasta de recuperação. Exemplo PowerShell, usando os dados **do projeto vazio de destino** em `restore.env`:

```powershell
docker run --rm --env-file ./restore.env --mount "type=bind,source=$PWD,target=/restore,readonly" postgres:17-bookworm psql -Atc "select tablename from pg_tables where schemaname='public'"
```

O resultado deve estar vazio. O comando seguinte substitui os objetos presentes no dump; execute somente após conferir que a conexão é a do novo projeto vazio:

```powershell
docker run --rm --env-file ./restore.env --mount "type=bind,source=$PWD,target=/restore,readonly" postgres:17-bookworm pg_restore --dbname=postgres --no-owner --no-acl --clean --if-exists --exit-on-error --single-transaction /restore/workmy-restore.dump
```

6. Confirme usuários, clientes, projetos e pagamentos pelo SQL Editor. Atualize conexão e CA do Render para o projeto recuperado, mantendo o JWT secret. Reative o deploy e publique. Migrations posteriores ao backup serão aplicadas no startup.
7. Apague as cópias locais não criptografadas e o arquivo de credenciais após a conferência. Conserve o backup criptografado e a senha em locais separados.

Não use o comando de restauração para mesclar dados em um banco existente. A CI testa dump/restauração em PostgreSQL descartável; a recuperação de um projeto Supabase real deve ser verificada antes de considerar seus dados importantes protegidos.

### Rollback da aplicação

Preferência: reverta a alteração problemática com `git revert <commit>`, revise e faça push para `main`; todo o pipeline será executado. Não reverta o arquivo de migration já aplicado: mantenha a cadeia de revisões e faça uma nova migration corretiva se necessário.

Em uma emergência, desabilite `CLOUD_DEPLOY_ENABLED`, identifique no resumo de Actions o último SHA bom e seus dois deployments. No Render, publique esse commit específico; aguarde o health check. Na Vercel, restaure o deployment de produção correspondente. Não misture versões aleatórias dos dois componentes. O schema não sofre downgrade automático. Depois registre a correção na `main` e reative o fluxo.

## 5. Reproduzir os checks com Docker local

Tudo abaixo usa o projeto **workmy-cloud-ci**, separado do Compose normal e com dados descartáveis. O frontend usa `https://localhost:8443`; os certificados são de teste e não devem ser reutilizados na nuvem. Execute na raiz do repositório, após instalar Python/uv, Node e iniciar Docker Desktop com containers Linux:

```powershell
uv sync --frozen --project backend-fastapi
npm --prefix frontend ci
npm --prefix deploy/ci ci
uv run --frozen --project backend-fastapi python deploy/ci/certgen.py
$env:VITE_API_BASE_URL='/api'
$env:VITE_CLOUD_DEMO='true'
npm --prefix frontend run build
docker compose --env-file deploy/ci/.env -f deploy/ci/compose.yml up -d --build --wait --wait-timeout 180
node deploy/ci/node_modules/playwright/cli.js install chromium
npm --prefix deploy/ci test
```

O navegador de teste aceita o certificado local de teste; o smoke em produção mantém a verificação HTTPS normal. Se o Chromium baixado não iniciar no Windows, rode `$env:PLAYWRIGHT_CHANNEL='chrome'` antes do teste para usar o Chrome instalado. Para encerrar e apagar **somente os dados desse projeto descartável**:

```powershell
docker compose --env-file deploy/ci/.env -f deploy/ci/compose.yml down -v
```

Para conferir memória: `docker stats --no-stream workmy-cloud-ci-cloud-1`. A imagem é executada com limite de 512 MiB. O teste cobre cadastro, recebimento, upload de 5 MiB, PDF/ZIP, refresh e logout; os passos adicionais da CI verificam recriação do container, queda do banco e restauração.

## 6. Diagnóstico

| Sintoma | Verificação/ação |
|---|---|
| Site abre, mas `/api` retorna HTML | Confirme rewrite antes do fallback SPA e `RENDER_URL` correto; publique novamente. |
| Login parece funcionar, mas volta ao login | Use a URL canônica da Vercel; confira os dois `Set-Cookie`, `Secure`, ausência de Domain e `VITE_API_BASE_URL=/api`. |
| `401` | Sessão inválida/expirada; confirme JWT secret permanente e conta smoke; entre novamente. |
| `403` por origem | Compare `APP_URL`, `APP_PUBLIC_URL`, `CORS_ORIGIN` e `CORS_ORIGINS`, incluindo HTTPS e ausência de barra final. Previews não estão liberados. |
| `404` em rota de página | Fallback SPA ausente; confira `vercel.json`. |
| `502/503` no começo | Aguarde o cold start; veja health check e logs Render. Se persistir, verifique Supabase pausado. |
| Health check falha | Leia os logs de startup/migration; confira senha, URL asyncpg, porta 5432 e CA. `/health` do BFF só verifica o Node; o check correto é `/api/health/ready`. |
| Erro IPv6 ou network unreachable | Use Session Pooler (host `*.pooler.supabase.com`), não a conexão direta `db.<ref>.supabase.co`. |
| Erro SSL/TLS do banco | Cole PEM completo, com quebras de linha reais; confira hostname do pooler. Não desligue a validação do certificado. |
| Prepared statement inválido | Confira se usou porta 6543 por engano. Use Session Pooler 5432. |
| `413` em upload | Confira limite Base64 de 8 MB no BFF e corpo até 5 MiB no arquivo. Não coloque o BFF em uma Vercel Function. |
| Exportação `422` / `429` | Reduza o período / aguarde a exportação ativa. |
| `ROUTER_EXTERNAL_TARGET_ERROR` | Limite do proxy Vercel; confira se o servidor despertou e o volume é adequado à demonstração. |
| Build Vercel procura `frontend/frontend` | Execute os comandos CLI da raiz do repositório; Root Directory do projeto deve ser `frontend`. |
| Versão publicada não é a testada | Desative Auto-Deploy Render e deploy Git Vercel; confira SHA no resumo e no health check. |
| Artifact de backup ausente | O job falhou antes da criptografia; confira secrets, CA, banco ativo e logs sem credenciais. |

## Referências oficiais

- [Evidências da validação local](evidencias/cloud-ci-2026-10-19/RELATORIO.md)
- [Cache de rewrites externos na Vercel](https://vercel.com/changelog/vercels-cdn-now-respects-cache-control-headers-from-external-origins-by-default)
- [Render Free e cold starts](https://render.com/docs/free)
- [Docker e porta pública Render](https://render.com/docs/web-services)
- [Deploy de um SHA específico](https://api-docs.render.com/reference/create-deploy)
- [Rewrites Vercel](https://vercel.com/docs/routing/rewrites)
- [Vercel com GitHub Actions](https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel)
- [Limites Vercel e uso Hobby](https://vercel.com/docs/plans/hobby)
- [Conexão Supabase/PostgreSQL](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Desativação da Data API](https://supabase.com/docs/guides/api/securing-your-api)
- [Backups Supabase](https://supabase.com/docs/guides/platform/backups)
