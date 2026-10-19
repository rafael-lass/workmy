# Validação local da implantação cloud — 19/10/2026

Implementação preparada para Vercel + Render + Supabase. Nenhum recurso nesses provedores foi criado/publicado nesta execução; a conexão real entre os provedores depende do preenchimento dos painéis e secrets descritos em [DEPLOY_CLOUD.md](../../DEPLOY_CLOUD.md).

## Ambiente e resultados

Windows, Python 3.12 local e Node 24 local; Docker Desktop com containers Linux. A imagem cloud usa Python 3.12 e Node 22, PostgreSQL de teste versão 17 e limite de memória de 512 MiB. Os dados são fictícios, exclusivos do projeto Compose `workmy-cloud-ci`.

| Verificação executada | Resultado |
|---|---|
| Suíte completa Python | 76 aprovados, 4 ignorados; testes opcionais da carga histórica exigem outro banco explicitamente configurado |
| Grupo Python após adicionar cenário de contagem/limite por usuário e período | 14 aprovados, incluindo 422, 429 e limpeza após cancelamento |
| Vitest | 27 aprovados |
| BFF Node test runner, inclusive após atualização de dependência | 7 aprovados |
| ESLint, TypeScript e build Vite | Aprovados |
| Build final do container cloud | Aprovado; npm audit do BFF sem vulnerabilidades |
| Playwright com Chrome instalado, proxy HTTPS local e banco via TLS | 2 aprovados |
| Migration baseline → head em PostgreSQL/TLS e `alembic check` | Aprovado, sem divergências de schema |
| Recriação do container da aplicação | Conta e pagamento preservados no banco |
| Queda real do PostgreSQL de teste | Endpoint de prontidão retornou 503 com corpo sanitizado; banco reiniciado em seguida |
| Encerramento do processo Node | Supervisor encerrou o container com código 1; recriação restaurou prontidão |
| Script real de backup, criptografia, descriptografia e pg_restore | Pagamento recuperado em outro banco descartável |
| actionlint dos workflows | Aprovado |
| `git diff --check` | Aprovado |

A jornada de navegador cobriu cadastro, cookies host-only/HttpOnly/Secure/SameSite=Strict, chamadas na mesma origem, recebimento, upload de 5 MiB, PDF, download ZIP, refresh, navegação direta/atualização de página e logout. O Chromium baixado não iniciou neste Windows; a opção `PLAYWRIGHT_CHANNEL=chrome` permitiu usar o Chrome instalado. O workflow Linux usa Chromium.

Uma amostra de `docker stats --no-stream`, após a jornada com upload e exportação, registrou **181,3 MiB de 512 MiB**. É uma observação pontual, não uma medição de pico, teste de carga ou garantia para qualquer volume.

O ensaio de restauração identificou que um banco PostgreSQL vazio já possui schema `public`. O comando de recuperação e o workflow foram ajustados para usar `--clean --if-exists --single-transaction` apenas no banco descartável/vazio selecionado.

## Limites e validações pendentes

- CI remoto, PostgreSQL 15 da matriz e os serviços reais Vercel/Render/Supabase serão verificados depois do push e da configuração pelo responsável.
- Os testes HTTPS locais reproduzem o proxy da Vercel, mas não substituem a comprovação dos dois `Set-Cookie` no domínio real. O workflow inclui um smoke autenticado para isso.
- O primeiro deploy permite ausência dos secrets de smoke para criar a conta de teste; o resumo informa que esse check foi ignorado. Depois é necessário cadastrar a conta e repetir o workflow.
- Ferramentas auxiliares de deploy usam Vercel CLI 64.5.0 travada em lockfile. O patch compatível `tar` 7.5.22 removeu o advisory crítico detectado. A auditoria ainda registra 32 avisos transitivos moderados/altos da ferramenta upstream; ela só é executada nos checks/deploy, não entra no frontend publicado nem no container da aplicação.
- Não foram executados testes de muitos usuários/exportações simultâneas ou migração de uma base pessoal. A configuração é para a demonstração pequena acordada.
