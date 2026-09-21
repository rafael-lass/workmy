# Glossário — siglas e termos

Lista de consulta do quadro WorkMy — Desenvolvimento.

## Siglas — organização, requisitos e testes

[Trello](https://trello.com/c/aBt7rYdl)

**WM — WorkMy:** prefixo que identifica os cartões do projeto. Ex.: WM-013 é a entrega sobre etapas dos projetos.

**PO — Product Owner (responsável pelo produto):** define prioridades e o que a solução precisa entregar. No grupo, Rafael.

**QA — Quality Assurance (garantia da qualidade):** organiza verificações para prevenir e encontrar problemas. Tais cuida de QA e documentação.

**RF — Requisito Funcional:** o que o sistema deve fazer. Ex.: exportar lançamentos financeiros.

**RNF — Requisito Não Funcional:** condição de qualidade ou operação. Ex.: isolamento dos dados por usuário e persistência após reiniciar.

**RN — Regra de Negócio:** restrição do domínio. Ex.: estorno exige motivo.

**CT — Caso de Teste:** roteiro com pré-condição, passos, resultado esperado e evidência. CT-WM014 testa a entrega WM-014.

**MVP — Minimum Viable Product (produto mínimo viável):** versão inicial com funções essenciais para validar a solução.

**E2E — End-to-End (ponta a ponta):** testa uma jornada completa, da tela até o banco. Está planejado no WM-018.

## Siglas — arquitetura, API e interface

[Trello](https://trello.com/c/iYr3oruP)

**API — Application Programming Interface (interface de programação de aplicações):** permite que partes do sistema troquem dados. Ex.: GET /api/dashboard/resumo.

**BFF — Backend for Frontend (servidor dedicado à interface):** camada Express entre o navegador e o FastAPI; cuida dos cookies, sessão e encaminhamento das requisições.

**CRUD — Create, Read, Update, Delete:** criar, consultar, atualizar e excluir. No WorkMy, clientes e outros registros usam exclusão lógica.

**DTO — Data Transfer Object (objeto de transferência de dados):** define os campos enviados ou recebidos entre camadas/API. Não é a própria tabela do banco.

**UI — User Interface (interface do usuário):** telas, botões e formulários.

**HTTP — Hypertext Transfer Protocol (protocolo de transferência de hipertexto):** regras de comunicação entre navegador e servidores. GET consulta; POST envia/cria ou executa uma ação.

**URL — Uniform Resource Locator (localizador uniforme de recurso):** endereço de uma página, endpoint ou arquivo.

**HTML — HyperText Markup Language:** linguagem que estrutura a página.

**CSS — Cascading Style Sheets (folhas de estilo em cascata):** define cores, espaçamento e apresentação da página.

**Endpoint:** não é sigla; é um endereço da API que oferece uma operação.

## Siglas — autenticação e segurança

[Trello](https://trello.com/c/snIdUVdw)

**JWT — JSON Web Token:** formato de token assinado usado para representar a autenticação. A assinatura permite detectar alterações; o conteúdo não é automaticamente criptografado.

**HS256 — HMAC com SHA-256:** algoritmo de assinatura dos tokens usado no projeto.

**HMAC — Hash-based Message Authentication Code:** código de autenticação de mensagem baseado em hash e uma chave secreta.

**SHA-256 — Secure Hash Algorithm de 256 bits:** algoritmo usado como parte dessa assinatura.

**Claims do JWT:** campos do token. **sub** (subject) identifica o usuário; **exp** (expiration) indica expiração; **jti** (JWT ID) identifica o token; **type** distingue sua finalidade no projeto.

**Access token:** token de acesso, usado para acessar rotas protegidas; validade atual de 15 minutos.

**Refresh token:** token de renovação, usado para obter novo access token; validade atual de sete dias.

**HTTP-only / HttpOnly:** atributo do cookie que impede sua leitura por JavaScript da página.

**Bearer:** forma de enviar o token no cabeçalho Authorization.

**bcrypt:** algoritmo de hash de senha; não é uma sigla a traduzir. O sistema confere a senha pelo hash, sem armazená-la em texto puro.

**401:** código HTTP de falha/ausência de autenticação. Não é sigla.

## Siglas — banco de dados e arquivos

[Trello](https://trello.com/c/PQZLkUoP)

**SQL — Structured Query Language (linguagem de consulta estruturada):** usada para consultar e alterar dados relacionais.

**PK — Primary Key (chave primária):** identifica um registro de forma única. Ex.: id do projeto.

**FK — Foreign Key (chave estrangeira):** relaciona um registro a outro. Ex.: projeto ligado a um cliente.

**ID — Identifier (identificador):** código que distingue um registro.

**N:N — muitos para muitos:** um serviço pode ter várias tags e uma tag pode aparecer em vários serviços. A tabela servico_tags faz a ligação.

**JSON — JavaScript Object Notation:** formato textual para dados estruturados. O editor armazena a descrição formatada nesse formato.

**CSV — Comma-Separated Values (valores separados por vírgula):** arquivo tabular. A exportação planejada do WorkMy usa ponto e vírgula como separador para facilitar a leitura com vírgula decimal.

**UTF-8 — Unicode Transformation Format de 8 bits:** codificação de texto que representa acentos e outros caracteres.

**BOM — Byte Order Mark (marca de ordem de bytes):** marcador no início do arquivo; no CSV UTF-8 planejado ajuda programas a reconhecer a codificação.

**PDF — Portable Document Format (formato de documento portátil):** usado na apresentação comercial do serviço.

**MiB — mebibyte:** unidade de tamanho; 1 MiB = 1.048.576 bytes. A capa do serviço aceita até 5 MiB.

## Siglas — desenvolvimento, validação e imagens

[Trello](https://trello.com/c/MsTHTQVF)

**CI — Continuous Integration (integração contínua):** verificações automáticas das alterações. No projeto, o GitHub Actions executa os jobs definidos no workflow.

**PR — Pull Request (solicitação de integração de alterações):** proposta de mudança no repositório, com diferenças para revisão antes de integrar.

**PNG — Portable Network Graphics:** formato de imagem aceito para capas.

**JPEG — Joint Photographic Experts Group:** nome do grupo que deu origem ao padrão de imagem; JPEG/JPG é aceito para capas.

**WebP:** nome de um formato de imagem aceito para capas; não precisa de expansão como sigla.

**Commit:** registro de uma versão no Git. O código 21274ca identifica a versão analisada no quadro.

**Build:** processo de preparar/compilar o aplicativo para execução ou distribuição.

**Lint:** análise automática do código para encontrar problemas e desvios de padrão.

**Mock:** substituto controlado de uma dependência no teste. Os testes de componentes simulam chamadas à API.

**Smoke test:** verificação básica de que o sistema inicia e responde. Não substitui uma jornada E2E.

**Trace:** registro detalhado da execução, útil para investigar falhas.

**Idempotência:** repetir a operação não duplica seu efeito. Ex.: faturar novamente o mesmo projeto/mês não deve criar outra mensalidade.

## Tradução — etapas, stack e termos do quadro

[Trello](https://trello.com/c/y8fBGoVJ)

**DISCOVERY:** código interno atualmente associado à etapa inicial; a interface planejada mostrará Planejamento.
**IN_PROGRESS:** Andamento.
**REVIEW:** Revisão.
**COMPLETED:** Finalizado.

**Stack:** conjunto de tecnologias do produto. No WorkMy: React na interface, Express no BFF, FastAPI na API e PostgreSQL no banco; Nginx serve a interface e Docker organiza a execução dos serviços.

**Frontend:** parte com que o usuário interage no navegador.
**Backend:** processamento no servidor, com validações e regras.
**Proxy:** intermediário que encaminha requisições; papel exercido pelo BFF.

**Migration:** alteração versionada da estrutura do banco. Alembic aplica essas mudanças.
**Baseline:** versão inicial usada como referência.
**Soft delete / exclusão lógica:** marca o registro como excluído, preservando-o no banco.
**Constraint:** regra imposta pelo banco, como impedir duplicidade.

**Healthcheck:** verificação de saúde/disponibilidade de um serviço.
**Workflow:** sequência de tarefas automatizadas.
**Job:** conjunto de passos executados no workflow.
**Thread:** unidade de execução; a geração de PDF usa uma thread para evitar bloquear diretamente o fluxo assíncrono.

Esta lista é material de consulta. Seus cartões não representam novas entregas do produto nem alteram os status WM-001 a WM-021.

