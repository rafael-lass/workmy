# Evidências técnicas do backlog WorkMy

Execução local em **21/09/2026**, fuso America/Sao_Paulo. Este registro sustenta a classificação do backlog e separa testes executados de inspeção de código.

## Versão e ambiente

- Commit-base: `21274ca1e45875375ff3e4bd4afb512b6de8daee`.
- Ambiente: Windows, PowerShell, Python **3.13.13** da `.venv` do backend e Node **22.18.0**.
- Backend: pytest sobre SQLite em memória/temporário e repositórios de teste; não utiliza banco pessoal.
- Frontend: Vitest **4.1.11**, jsdom e mocks das chamadas à API nos testes de componentes.
- O código funcional não foi alterado na preparação do quadro. A exclusão local preexistente de `render.yaml` foi preservada.
- Novos arquivos do backlog e relatórios são alterações locais; não houve commit, push ou execução remota do CI.

## Resultados

| Verificação | Resultado | Evidência |
| --- | --- | --- |
| Suíte backend | 39 aprovados; exit code 0; 9,24 segundos | [Log](backend.log) · [JUnit](backend.xml) |
| Suíte frontend | 15 aprovados em 9 arquivos; exit code 0; 9,65 segundos | [Log](frontend.log) · [JUnit](frontend.xml) |
| CT-WM017 previsão do próximo mês | Reprovado: obtido 1200.00; esperado 300.00 | [Log](previsao.log) · [Reprodutor](repro_previsao.py) |
| Docker, Compose e CI | Configuração inspecionada, execução integrada não realizada | Código indicado nos cartões WM-010 e WM-011 |
| Documentação existente | Revisada por leitura | WM-012 |

Os 54 testes aprovados não detectavam o defeito de previsão reproduzido separadamente. Não representam ausência de bugs, cobertura de 100%, validação externa ou aprovação de testes E2E.

## Comandos executados

Na pasta `backend-fastapi`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --junitxml=../docs/trello/evidencias/2026-09-21/backend.xml
```

Na pasta `frontend`:

```powershell
node node_modules/vitest/vitest.mjs run --reporter=default --reporter=junit --outputFile.junit=../docs/trello/evidencias/2026-09-21/frontend.xml
```

Na raiz do repositório, reprodução isolada do WM-017:

```powershell
.\backend-fastapi\.venv\Scripts\python.exe docs/trello/evidencias/2026-09-21/repro_previsao.py
```

As saídas foram capturadas com `Tee-Object`, preservando o código de saída dos processos de teste. O reprodutor é um diagnóstico: o resultado funcional aparece no log, e o sucesso do processo significa que o diagnóstico foi executado, não que o comportamento esteja correto.

## Limites da evidência

- Não foram executados nesta preparação Docker, PostgreSQL, E2E, lint, build ou pipeline remoto.
- Os testes de PDF verificam estrutura binária e contratos; não certificam visualmente todo documento possível.
- A configuração Docker e os documentos em Concluído são implementações existentes, sem alegação de verificação operacional completa nesta sessão.
- As etapas novas, a retirada dos percentuais, CSV, reorganização visual e correção de previsão permanecem em A fazer conforme o plano do quadro.
- Os relatórios não registram aprovação de Rafael, Gabriel ou Tais nem atribuem a eles execuções feitas pelo assistente.
- Relatórios JUnit e logs de ferramentas podem conter o caminho local do workspace; não contêm senhas de uso real ou tokens de sessão extraídos do ambiente.

## Próximas execuções

Guardar evidências da próxima versão em outro diretório datado e identificar o commit ou patch testado. Não sobrescrever este registro como se representasse a implementação futura.
