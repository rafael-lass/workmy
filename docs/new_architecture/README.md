# 📚 Documentação Técnica do Desenvolvedor - WorkMy API

Este documento reúne todas as especificações técnicas, diagramas de banco de dados, regras de negócio da máquina de faturamento e especificações de endpoints para desenvolvedores da plataforma WorkMy.

> [!TIP]
> Para obter uma análise aprofundada da arquitetura do sistema, separação de responsabilidades (MVC/REST), integração com a nuvem do **Supabase (PostgreSQL)**, caching de dados e decisões de design estruturadas de nível Staff, consulte o documento: [docs/ARCHITECTURE.md](file:///C:/Faculdade/2026/workmy/docs/ARCHITECTURE.md).

---

## 🗃️ Modelo de Dados & Banco de Dados (SQLite/PostgreSQL)

O banco de dados do WorkMy foi projetado com isolamento total por usuário através de chaves estrangeiras que vinculam todos os recursos diretamente ao modelo `Usuario` (`usuarios.Usuario`).

```
Usuario (AbstractUser)
  ├── Cliente (1:N)
  ├── Servico (1:N)
  └── Projeto (1:N) ── Pagamento (1:N)
```

### 1. Usuario (`usuarios.Usuario`)
Modelo SQLAlchemy que representa o usuário do sistema:
- `email`: `String` (único)
- `telefone`: `String`

### 2. Cliente (`gestao_freelas.Cliente`)
Cadastro comercial de clientes pertencentes ao usuário:
- `usuario_id`: `Integer` (ForeignKey)
- `nome`: `String(100)`
- `email`: `String`
- `telefone`: `String(20)`

### 3. Servico (`gestao_freelas.Servico`)
Catálogo de serviços oferecidos com suporte a tags e banner de mídia:
- `usuario_id`: `Integer` (ForeignKey)
- `nome`: `String(150)`
- `descricao`: `Text`
- `tags`: `String(250)` (separadas por vírgula para filtros rápidos)
- `ferramentas`: `String(250)` (tecnologias utilizadas)
- `github_repo`: `String`
- `imagem_bytes`: `LargeBinary` (dados da capa do serviço em Base64)
- `imagem_mime`: `String(50)` (Tipo MIME da capa)

### 4. Projeto (`gestao_freelas.Projeto`)
Representa um contrato/vínculo entre cliente e serviço:
- `usuario_id`: `Integer`
- `cliente_id`: `Integer`
- `servico_id`: `Integer`
- `status`: `String` (`DISCOVERY`, `IN_PROGRESS`, `REVIEW`, `COMPLETED`)
- `recorrencia_ativa`: `Boolean` (Indica se a cobrança recorrente está habilitada)
- `tipo_recorrencia`: `String` (`MENSAL`, `AVULSO`)
- `valor_mensal`: `Numeric` (Valor de cobrança mensal automatizada)
- `dia_vencimento`: `Integer` (Dia do mês de cobrança, entre 1-28)
- `recorrencia_inicio`: `Date` (Data de início do plano)
- `mensalista`: `Boolean` (Marcado automaticamente pelo sistema se há mensalidade configurada e ativa)

### 5. Pagamento (`gestao_freelas.Pagamento`)
Lançamentos financeiros de receitas associados a um Projeto:
- `projeto_id`: `Integer`
- `valor`: `Numeric`
- `tipo_pagamento`: `String` (`MENSAL` para mensalidades geradas e `AVULSO` para extras/manuais)
- `data`: `Date` (Data do recebimento ou vencimento)
- `referencia_mes`: `String` (Identificador temporal `YYYY-MM` para garantir a idempotência da recorrência)
- `gerado_automaticamente`: `Boolean`
- `comprovante_bytes`: `LargeBinary` (dados da imagem do comprovante anexado)
- `comprovante_mime`: `String(50)`
- `deletado_em`: `DateTime` (soft delete)

---

## ⚙️ Regras de Negócio: O Motor de Faturamento Recorrente

O fluxo financeiro do WorkMy foi projetado sob duas premissas fundamentais: **sem pré-geração em lote** e **idempotência estrita**.

### 1. Cobrança Recorrente sob Demanda
- Não existem dezenas de lançamentos futuros "vazios".
- A mensalidade é gerada **exclusivamente uma vez para o mês atual** (`referencia_mes = YYYY-MM`) quando:
  1. A recorrência está ativa (`recorrencia_ativa = True` e `tipo_recorrencia = 'MENSAL'`).
  2. O dia do mês atual é **igual ou maior** ao `dia_vencimento` programado.
  3. Não existe nenhum pagamento cadastrado para o projeto com o identificador de referência temporal do mês atual.
- Este fluxo é ativado no boot diário do sistema ou quando o usuário cria novos contratos/pagamentos.

### 2. Restrição de Lançamentos Manuais
- Formulários manuais de adição ou edição de pagamentos na interface criam lançamentos classificados estritamente como **Avulsos** (`AVULSO`).
- Isso evita que o faturamento de mensalidades seja gerado em duplicidade manual.

### 3. Previsão de Faturamento (`Previsão do Mês que Vem`)
- O cálculo da previsão de receitas para o mês seguinte é dinâmico e preciso:
  - Realiza a soma do `valor_mensal` de todos os projetos cuja recorrência está ativa no banco de dados.

---

## 🔌 API Endpoints (Base URL: `/api`)

Todos os endpoints da API FastAPI (exceto os de registro e login via Node.js BFF) exigem cabeçalho de autenticação JWT: `Authorization: Bearer <access_token>`. O BFF cuida de incluir esse cabeçalho extraindo do Cookie nas rotas originadas do navegador.

### 1. Autenticação (`/auth`)
- `POST /auth/register` - Cria uma nova conta de usuário.
- `POST /auth/login` - Autentica o usuário e retorna `access` e `refresh` tokens.
- `POST /auth/refresh` - Renova o `access_token` usando o `refresh_token`.
- `GET /auth/me` - Retorna informações da conta do usuário logado.

### 2. Clientes (`/clientes`)
- `GET /clientes/` - Lista todos os clientes (com lucro acumulado).
- `POST /clientes/` - Registra um novo cliente.
- `GET /clientes/{id}/detalhe` - Agrega cliente, serviços prestados, contratos e histórico financeiro em uma única requisição rápida.
- `PUT /clientes/{id}` - Atualiza dados do cliente (JSON).
- `DELETE /clientes/{id}` - Soft-delete do cliente.

### 3. Serviços (`/servicos`)
- `GET /servicos/` - Catálogo de serviços com suporte a busca e tags.
- `POST /servicos/` - Registra novo serviço (suporta imagem Base64).
- `GET /servicos/{id}/detalhe` - Retorna o serviço e todos os projetos vinculados.
- `PUT /servicos/{id}` - Atualiza serviço (JSON).
- `DELETE /servicos/{id}` - Soft-delete do serviço.

### 4. Projetos (`/projetos`)
- `GET /projetos/` - Lista todos os contratos com acumulado real.
- `POST /projetos/` - Cria novo contrato.
- `PATCH /projetos/{id}/mensalista` - Ativa ou pausa a recorrência mensal.
- `PUT /projetos/{id}` - Atualiza dados do contrato (JSON).
- `DELETE /projetos/{id}` - Soft-delete do contrato.

### 5. Pagamentos (`/pagamentos`)
- `GET /pagamentos/` - Histórico financeiro geral.
- `POST /pagamentos/` - Registra pagamento manual (Avulso).
- `PUT /pagamentos/{id}` - Atualiza valor ou dados (JSON).
- `DELETE /pagamentos/{id}` - Exclui lançamento financeiro.

### 6. Dashboard (`/dashboard`)
- `GET /dashboard/mensal` - Estatísticas financeiras agregadas, fluxo de caixa e previsto do mês.
- `GET /dashboard/previsao` - Lista detalhada de receitas previstas para o próximo mês.

---

## 🔒 Auditoria de Dados (`AuditLog`)
Toda ação de mutação de dados (`CREATE`, `UPDATE`, `DELETE`) nos modelos principais gera um registro de histórico de auditoria na tabela `AuditLog`, registrando:
- O usuário que realizou a alteração.
- O tipo e ID do recurso mutado.
- O estado anterior (`dados_anterior` em JSON) e o novo estado (`dados_novo` em JSON).

---

## 🧪 Estrutura de Testes Automatizados
O backend possui suíte de testes unitários e de integração robusta em Pytest. O padrão abrange testes In-Memory (mocks) e testes End-to-End da API FastAPI.
Para executar as validações locais:
```bash
cd backend-fastapi
uv sync
.\.venv\Scripts\pytest
```
