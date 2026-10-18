# Requisitos funcionais — WorkMy

[Índice](README.md) · [Funcionais](REQUISITOS_FUNCIONAIS.md) · [Não funcionais](REQUISITOS_NAO_FUNCIONAIS.md) · [Regras de negócio](REGRAS_DE_NEGOCIO.md)

**Atualização:** 21/09/2026 · **Base:** `21274ca` + correção local WM-017, ainda sem commit/push.

## Objetivo e público

O WorkMy atende profissionais autônomos e pequenos prestadores que precisam organizar clientes, serviços, projetos e recebimentos. Os requisitos funcionais descrevem **o que o sistema permite fazer**.

## Funcionalidades implementadas

“Implementado” identifica comportamento existente no código; o alcance da validação está nos relatórios de teste.

| ID | Requisito funcional | Situação |
| --- | --- | --- |
| RF-01 | Permitir cadastro, login por usuário ou e-mail, consulta da sessão e logout. | Implementado |
| RF-02 | Cadastrar, consultar, editar e excluir logicamente clientes. | Implementado |
| RF-03 | Cadastrar e gerenciar serviços com descrição formatada, capa e tags. | Implementado |
| RF-04 | Gerar apresentação comercial de um serviço em PDF. | Implementado |
| RF-05 | Criar projetos vinculados a um cliente e a um serviço, com contratação avulsa ou mensal. | Implementado |
| RF-06 | Consultar e atualizar projetos, controlar suas etapas e arquivá-los. | Implementado |
| RF-07 | Configurar, pausar e retomar a recorrência de projetos mensais. | Implementado |
| RF-08 | Gerar cobranças mensais vencidas por uma ação manual de faturamento. | Implementado |
| RF-09 | Registrar recebimentos avulsos e confirmar o recebimento de cobranças pendentes. | Implementado |
| RF-10 | Cancelar cobranças pendentes e estornar recebimentos, informando o motivo. | Implementado |
| RF-11 | Consultar lançamentos financeiros com filtros e paginação; editar observação e comprovante. | Implementado |
| RF-12 | Exibir indicadores financeiros, série dos últimos seis meses e recebimentos recentes no dashboard. | Implementado |

## Detalhes dos fluxos

- **Autenticação:** telefone brasileiro opcional no cadastro; consulta da sessão pelo servidor.
- **Clientes:** nome obrigatório; empresa, e-mail e telefone opcionais; consulta do total recebido.
- **Serviços:** editor Tiptap com títulos, negrito, itálico, listas, citações e links; catálogo privado de tags reutilizáveis; visualização completa e PDF A4.
- **PDF comercial:** permite revisar nome, e-mail e telefone antes do download sem alterar a conta; usa o serviço salvo e não inclui dados financeiros ou de clientes.
- **Projetos:** a versão atual começa em Planejamento e segue Andamento, Revisão e Finalizado, sem progresso percentual. Arquivamento é uma ação separada com confirmação. Projetos arquivados podem ser reativados em Planejamento e consultados por um filtro próprio. As transições permitidas estão em [RN-08](REGRAS_DE_NEGOCIO.md#etapas-atuais-dos-projetos).
- **Recebimento avulso:** escolher serviço e depois cliente com projeto vinculado; clientes de outros serviços e projetos arquivados não aparecem na seleção.
- **Financeiro:** filtros por status, tipo, cliente, projeto, período e busca, com paginação. Não há edição ou exclusão genérica de pagamentos: cada operação respeita seu estado.
- **Faturamento:** geração acionada manualmente pela interface/API; não é uma rotina automática em segundo plano.
- **Dashboard:** a previsão do próximo mês já utiliza o primeiro vencimento elegível após a correção local WM-017. Revisão funcional de Tais pendente.

## Evoluções planejadas

| Entrega | Situação | Cartão |
| --- | --- | --- |
| Exportação CSV autenticada e filtrada no backend | A fazer | WM-014 |
| Download CSV pela interface financeira | A fazer | WM-015 |
| Ações rápidas no topo do dashboard e remoção de botões redundantes | A fazer | WM-016 |

Essas evoluções não são apresentadas como funcionalidades entregues. O botão Novo projeto já foi removido da navbar; permanece disponível nas páginas de Projetos, Dashboard e detalhe do cliente.

## Fora do escopo atual

Pagamentos parciais, gateway de pagamentos, emissão fiscal, recuperação de senha, faturamento automático em segundo plano, RabbitMQ, vínculo em massa, indicadores de leads, propostas personalizadas, colaboração em tempo real e funcionalidades completas do Notion. CSV está planejado na próxima versão, conforme a tabela acima.

## Evidências e documentos relacionados

[Relatório do reteste WM-017](trello/evidencias/2026-09-21-reteste-WM017/RELATORIO.md) · [Inventário dos 70 testes](trello/evidencias/2026-09-21-reteste-WM017/INVENTARIO.md)

[Regras de negócio](REGRAS_DE_NEGOCIO.md) · [Arquitetura](ARQUITETURA.md) · [Detalhamento de serviços](SERVICOS.md)
