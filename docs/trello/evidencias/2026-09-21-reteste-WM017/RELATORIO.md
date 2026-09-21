# Relatório de testes — WorkMy / N1 PMI

## 1. Identificação

- Data: 21/09/2026; ambiente local Windows/PowerShell.
- Versão: commit-base `21274ca1e45875375ff3e4bd4afb512b6de8daee` mais alterações locais do WM-017, ainda sem commit/push. O arquivo `manifesto.json` identifica os arquivos testados por SHA-256.
- Python 3.13.13; Node 22.18.0; Vitest 4.1.11.
- Execução automatizada pelo assistente. Revisão funcional de Tais: **pendente**.
- Escopo: regra de previsão financeira, calendário compartilhado e regressão das funcionalidades existentes.

## 2. Resumo dos resultados

| Execução | Executados | Aprovados | Reprovados | Evidência |
| --- | ---: | ---: | ---: | --- |
| Novos cenários de integração antes da correção | 14 | 10 | 4 | [Log](antes.log) / [JUnit](antes.xml) |
| Backend completo após correção | 55 | 55 | 0 | [Log](backend.log) / [JUnit](backend.xml) |
| Frontend completo após correção | 15 | 15 | 0 | [Log](frontend.log) / [JUnit](frontend.xml) |
| Diagnóstico CT-WM017 após correção | 1 | 1 | 0 | [Resultado](previsao.log) |

Resultado final das suítes: **70 testes aprovados, zero falhas, zero erros e zero ignorados**. O diagnóstico adicional repete o cenário principal e não é somado aos 70. Backend: 14,62 segundos; frontend: 13,20 segundos nesta execução paralela. Tempos não são métricas de desempenho do produto.

Os 54 testes anteriores continuaram aprovados. Foram acrescentados 16 testes: 14 integrações e duas verificações da regra de calendário. A contagem inicial de quatro falhas pertence à execução proposital anterior à correção, preservada para demonstrar que os testes detectam o defeito.

## 3. Defeito, causa e solução

O dashboard somava todos os contratos mensais ativos sem considerar quando poderiam vencer pela primeira vez. Isso incluía R$ 900 de um contrato iniciado em novembro na previsão de outubro.

A regra de primeiro vencimento foi extraída para o domínio e compartilhada entre faturamento e dashboard. A previsão soma apenas contratos cujo primeiro vencimento ocorre antes do início do mês posterior ao previsto. Como os contratos elegíveis são mensais e ativos, eles possuem vencimento no mês previsto a partir desse primeiro vencimento.

O início explícito prevalece; quando ausente, usa-se a criação; se ambos estiverem ausentes, usa-se a data de referência. Foram mantidos os filtros de usuário, recorrência ativa, modalidade mensal, status e exclusão lógica. A consulta seleciona somente valor e datas necessários. Não houve migration nem alteração do contrato HTTP.

| Caso principal CT-WM017 | Antes | Depois |
| --- | --- | --- |
| Referência 21/09/2026; R$ 300 desde setembro e R$ 900 desde novembro; vencimento dia 5 | Obtido R$ 1.200: REPROVADO | Obtido R$ 300: APROVADO |

Evidência histórica: [diagnóstico original](../2026-09-21/previsao.log). O reprodutor original é preservado: sua última frase “nenhuma correção aplicada” significa que o próprio script não modifica o código; nesta rodada ele foi executado sobre a aplicação já corrigida.

## 4. Casos da correção

**Pré-condição comum das integrações:** banco SQLite em memória novo por teste, usuários A/B, clientes e serviços de teste; nenhum dado pessoal de desenvolvimento. **Passos comuns:** preparar os contratos indicados, executar `PostgresDashboardQuery.get_resumo` como A com data fixa, conferir `previsto_proximo_mes`. Os testes também preservam o tipo textual do campo nos quatro cenários principais.

| ID | Cenário / dados | Resultado esperado e obtido | Status |
| --- | --- | --- | --- |
| CT-WM017-01 | Setembro; R$ 300 vigente + R$ 900 desde 01/11 | Outubro: R$ 300 | APROVADO |
| CT-WM017-02 | Segundo contrato começa em 01/10, vence dia 5 | Outubro: R$ 1.200 | APROVADO |
| CT-WM017-03 | Segundo contrato começa no vencimento, 05/10 | Outubro: R$ 1.200 | APROVADO |
| CT-WM017-04 | Segundo contrato começa em 06/10 | Outubro: R$ 300 | APROVADO |
| CT-WM017-05 | R$ 300 vigente + R$ 900 pausado | Outubro: R$ 300 | APROVADO |
| CT-WM017-06 | Segundo contrato finalizado | Outubro: R$ 300 | APROVADO |
| CT-WM017-07 | Segundo contrato arquivado | Outubro: R$ 300 | APROVADO |
| CT-WM017-08 | Segundo contrato excluído logicamente | Outubro: R$ 300 | APROVADO |
| CT-WM017-09 | Segundo contrato pertence a B | Previsão de A: R$ 300 | APROVADO |
| CT-WM017-10 | Segundo contrato avulso e sem recorrência | Outubro: R$ 300 | APROVADO |
| CT-WM017-11 | Contrato de R$ 900 sem início explícito, criado em 05/10 | Outubro: R$ 900 | APROVADO |
| CT-WM017-12 | Mesmo cenário, criado em 06/10 | Outubro: zero | APROVADO |
| CT-WM017-13 | Referência dezembro; dois contratos de R$ 900, inícios 05/01 e 06/01, vencimento 5 | Janeiro: R$ 900 | APROVADO |
| CT-WM017-14 | Nenhum contrato | Zero | APROVADO |
| CT-WM017-15 | Regra isolada: início e criação ausentes, referência 21/12, vencimento 5 | Primeiro vencimento em 05/01 do ano seguinte | APROVADO |
| CT-WM017-16 | Regra isolada: início 05/10, criação 01/11, referência setembro | Primeiro vencimento em 05/10; início explícito prevalece | APROVADO |

Casos 15/16: preparar as datas indicadas, chamar `first_due_date` diretamente e comparar a data retornada. A ausência de criação é testada no domínio porque a coluna persistida exige uma data.

Implementação dos casos: [integração](../../../../backend-fastapi/tests/integration/test_dashboard_forecast.py) e [domínio](../../../../backend-fastapi/tests/domain/test_recorrencia.py). Evidência individual: [inventário dos 70 testes](INVENTARIO.md), nomes e resultados extraídos dos relatórios JUnit.

## 5. Regressão das funcionalidades existentes

| Grupo | Verificações e documentação dos casos |
| --- | --- |
| Autenticação | Cadastro, duplicidade, login, refresh, perfil e sessão React: [CT-WM001](../../cards/WM-001.md) |
| Clientes | Campos inválidos e preservação após falha: [CT-WM002](../../cards/WM-002.md) |
| Serviços e PDF | Documento, tags, propriedade, PDF e download: [CT-WM003](../../cards/WM-003.md), [CT-WM004](../../cards/WM-004.md) |
| Projetos | Criação, colisão, validações e proteção do histórico: [CT-WM005](../../cards/WM-005.md) |
| Recorrência | Idempotência, início futuro, pausa e retomada sem meses pausados: [CT-WM006](../../cards/WM-006.md) |
| Financeiro e dashboard | Estados, valores, motivos, atraso e totais após estorno: [CT-WM007](../../cards/WM-007.md), [CT-WM008](../../cards/WM-008.md) |
| Migration | Preservação de dados legados e deduplicação de tags: [CT-WM009](../../cards/WM-009.md) |

Esses cartões detalham pré-condições, passos e expectativas históricas; os resultados desta nova execução estão nos JUnit deste diretório. A preservação de 70 testes aprovados não representa cobertura total nem validação externa.

## 6. Reprodução

Na pasta `backend-fastapi`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --junitxml=../docs/trello/evidencias/2026-09-21-reteste-WM017/backend.xml
```

Na pasta `frontend`:

```powershell
node node_modules/vitest/vitest.mjs run --reporter=default --reporter=junit --outputFile.junit=../docs/trello/evidencias/2026-09-21-reteste-WM017/frontend.xml
```

Na raiz:

```powershell
backend-fastapi/.venv/Scripts/python.exe docs/trello/evidencias/2026-09-21/repro_previsao.py
```

Os comandos foram capturados com `Tee-Object`, preservando o código de saída na rodada final. Use um novo diretório ao repetir para não sobrescrever evidências. O diagnóstico retorna sucesso de processo mesmo diante de divergência; a asserção que impede regressão está no pytest.

## 7. Não executado e limites

Quatro frentes permanecem pendentes: E2E com Docker/PostgreSQL (WM-018), migrations/concorrência em PostgreSQL (WM-019), testes completos do proxy e refresh do BFF (WM-020) e revisão funcional humana de Tais. São frentes, não quatro testes individuais já especificados/executados.

Também não foram executados teste de carga, validação com usuários externos ou pipeline remoto. API e persistência foram exercitadas em SQLite; componentes React usam jsdom e mocks. PDF é validado estruturalmente, sem certificação visual completa. Nenhuma aprovação humana foi presumida.

## 8. Resumo para o vídeo

“Executamos testes de regras de negócio, API, persistência e componentes da interface. Criamos 16 novos testes para a previsão financeira e regras de calendário. Antes da correção, quatro cenários falhavam porque contratos futuros entravam no mês errado. Compartilhamos a regra de vencimento entre faturamento e dashboard e repetimos a validação. O cenário principal passou de R$ 1.200 incorretos para R$ 300, como esperado. A rodada final teve 55 testes de backend e 15 de frontend aprovados. Guardamos logs e relatórios com o antes e depois. A jornada completa com PostgreSQL e a revisão funcional humana ainda estão pendentes.”
