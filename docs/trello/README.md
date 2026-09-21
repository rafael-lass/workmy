# WorkMy — Desenvolvimento

Backlog técnico do produto WorkMy. Implementações existentes em Concluído e próximas entregas em A fazer; não inclui organização da apresentação acadêmica.

Base: `21274ca1e45875375ff3e4bd4afb512b6de8daee` · Análise: 2026-09-21

Fonte editável: [board.json](board.json). Este arquivo e os cartões são gerados por `render_board.py`.

Quadro publicado: [https://trello.com/b/7Xv1gpIY/workmy-desenvolvimento](https://trello.com/b/7Xv1gpIY/workmy-desenvolvimento). Mapeamento e conferência: [publicacao.json](publicacao.json).

## Fluxo

A fazer → Em desenvolvimento → Em teste → Concluído · Bloqueado para impedimentos.

## Como interpretar os estados

Concluído identifica implementação existente revisada no código; o cartão delimita a evidência disponível. Não equivale a validação completa em navegador/PostgreSQL.
A fazer contém trabalho planejado, sem implementação realizada nesta preparação do backlog. WM-017 corrigido localmente e movido para Em teste, aguardando revisão funcional de Tais.
Os 12 cartões concluídos são uma classificação retrospectiva, não um histórico de movimentações. Não foram presumidos autores nem datas de entrega.
A base de testes foi executada novamente em 21/09/2026: 39 testes backend e 15 frontend aprovados. Não foram executados Docker, E2E, lint/build ou CI remoto nesta preparação.
Reteste WM-017: 55 backend e 15 frontend aprovados; evidências separadas em 2026-09-21-reteste-WM017. A execução anterior permanece histórica.

## A fazer (8)

- [WM-013 — Reformular ciclo de vida dos projetos e remover progresso percentual](cards/WM-013.md)
- [WM-014 — Criar exportação CSV autenticada no backend financeiro](cards/WM-014.md)
- [WM-015 — Integrar download CSV aos filtros do Financeiro](cards/WM-015.md)
- [WM-016 — Centralizar ações rápidas e remover botões duplicados](cards/WM-016.md)
- [WM-018 — Automatizar jornada completa no navegador contra o Docker](cards/WM-018.md)
- [WM-019 — Validar migrations e concorrência usando PostgreSQL](cards/WM-019.md)
- [WM-020 — Cobrir renovação de sessão e proxy binário do BFF](cards/WM-020.md)
- [WM-021 — Atualizar especificação técnica e rastrear requisitos até os testes](cards/WM-021.md)

## Em desenvolvimento (0)

Nenhum cartão nesta classificação inicial.


## Em teste (1)

- [WM-017 — Corrigir previsão financeira para respeitar o início da recorrência](cards/WM-017.md)

## Concluído (12)

- [WM-001 — Implementar autenticação JWT e sessão web pelo BFF](cards/WM-001.md)
- [WM-002 — Implementar CRUD de clientes com exclusão lógica](cards/WM-002.md)
- [WM-003 — Implementar catálogo de serviços com descrição formatada e tags](cards/WM-003.md)
- [WM-004 — Gerar apresentação comercial do serviço em PDF](cards/WM-004.md)
- [WM-005 — Implementar projetos vinculados a cliente e serviço](cards/WM-005.md)
- [WM-006 — Implementar faturamento mensal idempotente](cards/WM-006.md)
- [WM-007 — Implementar estados e regras dos lançamentos financeiros](cards/WM-007.md)
- [WM-008 — Implementar dashboard e agregações financeiras](cards/WM-008.md)
- [WM-009 — Versionar banco e migrar serviços preservando dados existentes](cards/WM-009.md)
- [WM-010 — Containerizar frontend, BFF, API e PostgreSQL](cards/WM-010.md)
- [WM-011 — Configurar testes automatizados e integração contínua](cards/WM-011.md)
- [WM-012 — Documentar instalação, arquitetura e operação do sistema](cards/WM-012.md)

## Bloqueado (0)

Nenhum cartão nesta classificação inicial.


## Responsabilidades futuras

- Rafael: PO e desenvolvimento; regras, API, banco e consolidação da versão.
- Gabriel: frontend e validação técnica; interface, BFF e E2E.
- Tais: QA e documentação; revisão funcional, requisitos e rastreabilidade.

Não atribuir autores ou datas às entregas passadas sem confirmação. Não convidar pessoas nem enviar notificações como parte da preparação local.

## Critério de conclusão para novos cartões

1. Implementação vinculada a commit ou PR, sem inventar publicação inexistente.
2. Critérios de aceite atendidos e verificados.
3. Testes relevantes aprovados com comando, ambiente, versão, data e resultado.
4. Revisão funcional de Tais registrada quando houver interface/regra; não marcar revisão humana sem confirmação.
5. Documentação do comportamento atualizada.

## Ordem recomendada

WM-013 → WM-014 → WM-015 → WM-016 → WM-017 → WM-021. WM-018, WM-019 e WM-020 compõem a evolução técnica seguinte.

## Evidências e reprodução

- [Relatório da análise e execução](evidencias/2026-09-21/RELATORIO.md)
- [Correção WM-017 e relatório de testes para N1](evidencias/2026-09-21-reteste-WM017/RELATORIO.md)
- [Log backend](evidencias/2026-09-21/backend.log) · [JUnit backend](evidencias/2026-09-21/backend.xml)
- [Log frontend](evidencias/2026-09-21/frontend.log) · [JUnit frontend](evidencias/2026-09-21/frontend.xml)

## Manutenção

Edite `board.json`, execute `python docs/trello/render_board.py` na raiz e confira com `python docs/trello/render_board.py --check`.

O JSON é uma fonte local estruturada, não um arquivo de importação nativa do Trello. Cada Markdown contém a descrição completa para o cartão correspondente. A publicação remota deve conservar IDs, listas, descrições e checklists, evitando duplicatas por ID WM.

O quadro trata do software. Ficha, vídeo, entrega acadêmica e apresentação não são cartões deste backlog.
