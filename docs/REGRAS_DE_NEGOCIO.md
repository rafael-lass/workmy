# Regras de negócio — WorkMy

[Índice](README.md) · [Funcionais](REQUISITOS_FUNCIONAIS.md) · [Não funcionais](REQUISITOS_NAO_FUNCIONAIS.md) · [Regras de negócio](REGRAS_DE_NEGOCIO.md)

**Atualização:** 21/09/2026 · **Base:** `21274ca` + correção local WM-017, ainda sem commit/push.

## Finalidade

As regras de negócio definem **as condições e restrições** que as funcionalidades devem respeitar. Os identificadores RN-01 a RN-19 correspondem ao material da N1; RN-20 registra a previsão financeira corrigida.

## Catálogo de regras

| ID | Regra de negócio |
| --- | --- |
| RN-01 | Cada usuário acessa somente seus próprios dados. Cliente e serviço usados em um projeto devem pertencer ao usuário autenticado. |
| RN-02 | Usuário e e-mail de cadastro devem ser únicos. |
| RN-03 | Cliente exige nome. A aplicação rejeita nomes repetidos para o mesmo usuário; essa validação não equivale a uma restrição de unicidade concorrente no banco. |
| RN-04 | Serviço exige nome único por usuário entre os registros não excluídos. |
| RN-05 | Serviço aceita descrição com até 20 mil caracteres, até dez tags e capa PNG, JPEG ou WebP de até 5 MiB. |
| RN-06 | Clientes e serviços vinculados a projetos não excluídos não podem ser excluídos. |
| RN-07 | Não pode existir outra contratação não excluída com a mesma combinação de usuário, cliente e serviço. |
| RN-08 | Projetos seguem transições de etapa permitidas. Concluir ou arquivar um projeto pausa sua recorrência. |
| RN-09 | Projeto com histórico financeiro não pode ser excluído; deve ser arquivado para preservar o histórico. |
| RN-10 | Recebimento manual nasce como AVULSO/PAGO. Mensalidade gerada nasce como PENDENTE. |
| RN-11 | Um lançamento pendente pode ser recebido ou cancelado. Um lançamento pago pode ser estornado. Cancelado e estornado são estados finais. |
| RN-12 | Cancelamento e estorno exigem motivo. |
| RN-13 | Valores devem ser positivos. Não há pagamento parcial nem alteração do valor original do lançamento. Recebimento com data futura é rejeitado. |
| RN-14 | Após a criação, a edição de detalhes permite alterar observação e comprovante, preservando o valor. |
| RN-15 | Um lançamento está atrasado quando permanece pendente e seu vencimento é anterior à data de negócio em São Paulo. |
| RN-16 | Totais recebidos consideram somente lançamentos PAGO; valores estornados deixam de integrar o realizado. |
| RN-17 | Cada projeto pode ter apenas uma mensalidade por referência AAAA-MM. Repetir o faturamento não deve duplicar cobranças. |
| RN-18 | Pausar a recorrência não cancela pendências existentes. Retomar exige nova data inicial; os meses pausados não são gerados. |
| RN-19 | Alterações no valor ou vencimento da recorrência afetam cobranças futuras, preservando os lançamentos existentes. |
| RN-20 | A previsão do próximo mês soma somente contratos mensais ativos com primeiro vencimento elegível até o fim do mês previsto. Exclui pausados, finalizados, arquivados, excluídos e dados de outro usuário. A regra de vencimento é compartilhada com o faturamento. |

## Etapas atuais dos projetos

O projeto nasce em **Planejamento**. Não há percentual de progresso na interface, no domínio ou na API. A coluna legada permanece no banco, sem atualização funcional, para preservar os dados antigos.

| Etapa atual | Código | Próximas etapas permitidas |
| --- | --- | --- |
| Planejamento | `DISCOVERY` | Andamento ou Arquivado |
| Andamento | `IN_PROGRESS` | Revisão ou Arquivado |
| Revisão | `REVIEW` | Andamento, Finalizado ou Arquivado |
| Finalizado | `COMPLETED` | Arquivado |
| Arquivado | `ARCHIVED` | Planejamento, pela ação Reativar |

Finalizar ou arquivar pausa a recorrência. Arquivar é uma ação separada com confirmação, não uma opção do seletor de etapas. Projetos finalizados ou arquivados não podem retomar recorrência. Os códigos internos foram preservados, sem migration.

## Estados financeiros

| Estado de origem | Operação | Estado de destino | Condição |
| --- | --- | --- | --- |
| PENDENTE | Receber | PAGO | Recebimento válido, sem data futura |
| PENDENTE | Cancelar | CANCELADO | Motivo obrigatório |
| PAGO | Estornar | ESTORNADO | Motivo obrigatório |

`CANCELADO` e `ESTORNADO` são terminais. Atraso é uma condição calculada, não um novo estado persistido. Somente `PAGO` compõe os totais recebidos.

## Recorrência e previsão

- O dia de vencimento mensal deve estar entre **1 e 28**.
- O primeiro vencimento ocorre no dia contratado do mês inicial se ainda não passou; caso contrário, no mês seguinte.
- O início explícito prevalece. Quando ausente, usa-se a data de criação; se ambas estiverem ausentes, usa-se a data de referência.
- Ao criar um projeto mensal com recorrência ativa, o sistema gera automaticamente as mensalidades com vencimento desde o início informado até hoje, inclusive. Todas nascem como `PENDENTE`, sem data de pagamento; vencimentos anteriores a hoje aparecem como atrasados.
- Exemplo: criação em 19/10/2026, início em 01/04/2026 e vencimento dia 5 gera abril a outubro (sete cobranças). Com vencimento dia 20, gera abril a setembro (seis cobranças), pois 20/10 ainda não chegou. Se o início for posterior ao vencimento do primeiro mês, a primeira cobrança fica para o mês seguinte.
- A geração manual cria as referências vencidas e ausentes desde o início ou retomada até a data atual.
- A combinação `(projeto_id, referencia_mes)` possui restrição única no banco.
- Retomar exige valor, vencimento e nova data inicial; meses pausados não são gerados.
- Projetos avulsos existentes podem habilitar cobrança mensal pela ação **Ativar mensal**. A ativação exige valor mensal, dia de vencimento e início, e gera as referências já vencidas desde a data escolhida. **Pausar** desativa novas cobranças e preserva recebimentos e pendências; **Retomar** reativa a cobrança a partir da nova data informada. Projetos finalizados ou arquivados continuam impedidos de ativar recorrência.
- **Exemplo da RN-20:** em 21/09/2026, um contrato vigente de R$ 300 e outro de R$ 900 iniciado em novembro geram previsão de outubro de **R$ 300**.

## Validações de serviços e anexos

- Descrição: documento JSON versionado com até 20 mil caracteres, sem HTML arbitrário ou imagens embutidas; links HTTP(S) e mailto.
- Tags: até dez por serviço, até 40 caracteres por nome; normalização de espaços e caixa. Remover a seleção de uma tag não exclui a tag do catálogo.
- Capa: PNG, JPEG ou WebP de até 5 MiB.
- Comprovante: PDF, PNG, JPEG ou WebP de até 5 MB.
- Campos legados de serviços e seus dados são preservados; repositório e ferramentas não são expostos na interface atual.

## Evidências e limitações

[Relatório do reteste WM-017](trello/evidencias/2026-09-21-reteste-WM017/RELATORIO.md) · [Inventário dos 70 testes](trello/evidencias/2026-09-21-reteste-WM017/INVENTARIO.md)

A RN-20 passou no reteste automatizado; revisão funcional de Tais pendente. Os testes de integração usam SQLite. A existência de restrições no banco não comprova, por si só, execução concorrente validada em PostgreSQL.

## Reativação e seleção de recebimento

Reativar um projeto arquivado o devolve a Planejamento, preserva seu histórico e mantém a recorrência pausada até uma retomada explícita. Projetos arquivados sem lançamentos podem ser excluídos logicamente; o histórico financeiro continua impedindo exclusão.

Arquivados são consultados pelo filtro Situação do projeto, separado das quatro etapas. No recebimento avulso, seleciona-se primeiro um serviço com projeto não arquivado e depois um cliente vinculado a esse serviço. O lançamento continua associado ao projeto correspondente; mudar o serviço limpa o cliente escolhido.
