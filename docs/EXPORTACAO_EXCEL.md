# Exportação Excel com multiprocessing por blocos

No dashboard, escolha 3, 6, 12 meses ou Total e clique em **Baixar planilhas**. O download é um ZIP com quatro Excel independentes: Pagamentos, Clientes, Serviços e Projetos. Cada arquivo contém uma aba; não há aba de dashboard.

## Objetivo e comparação justa

O sequencial e o paralelo executam exatamente as mesmas tarefas, com os mesmos dados, blocos, formatos e compressão. Não há `sleep`, cálculos descartáveis ou tratamento mais lento reservado ao sequencial. A diferença é o executor: uma chamada após a outra ou até quatro processos Python reais (`multiprocessing.get_context("spawn").Pool`).

A versão anterior distribuía um arquivo por processo. Quase todo o trabalho estava nos 200 mil pagamentos, deixando os outros processos ociosos. Agora os pagamentos também são divididos em blocos de 25 mil linhas: oito tarefas grandes, além dos cadastros. O Excel final continua sendo um único arquivo de pagamentos.

## Etapas chamadas por run()

1. `ExportarDashboardUseCase.run()` consulta os dados do usuário em uma transação REPEATABLE READ. São quatro projeções SQL, uma por conjunto, com o mesmo caminho nos dois modos. A transação termina antes de criar arquivos.
2. `DashboardExcelRenderer.render()` prepara templates com XlsxWriter e divide as linhas em blocos. Os blocos ficam em arquivos temporários privados; a fila dos processos recebe caminhos pequenos, em vez de copiar toda a lista de pagamentos.
3. `excel_rows.render_rows()` lê um bloco, calcula atraso, traduz etapas, converte a descrição formatada do serviço e serializa as células para XML do formato XLSX. Trata datas, moeda e texto literal, preservando a proteção contra fórmulas.
4. No modo sequencial, a função processa um bloco por vez. No paralelo, até quatro processos executam blocos independentes. Nenhum processo acessa o banco ou compartilha um workbook.
5. O processo principal reúne os fragmentos na ordem dos offsets originais e monta cada XLSX com os estilos e cabeçalhos gerados pelo XlsxWriter. A reunião não depende da ordem em que os workers terminam.
6. Os quatro arquivos são empacotados no ZIP, sem recomprimir arquivos já compactados. Temporários são removidos tanto no sucesso quanto em falhas.

O XML usado é o conteúdo interno padronizado de uma planilha XLSX. Apenas as linhas de dados são geradas em blocos; os demais componentes do workbook são produzidos pelo XlsxWriter. A linha técnica usada para identificar os estilos do template nunca entra no arquivo final.

A leitura do banco foi simplificada para a mesma sessão nos dois modos. O experimento anterior com quatro sessões e snapshot exportado foi substituído: não ajudava a dividir o principal custo, que era a planilha de pagamentos. A API continua usando o modo paralelo por padrão.

## Períodos e filtros

- `3`, `6`, `12`: meses de calendário incluindo o atual, até a data da exportação em America/Sao_Paulo. Em 08/10/2026, três meses correspondem a 01/08/2026 até 08/10/2026.
- Pagamentos são filtrados pelo vencimento, com limites inclusivos. Os cadastros são os relacionados aos pagamentos selecionados.
- `total`: todos os pagamentos e cadastros da conta, inclusive cadastros sem pagamentos e histórico excluído logicamente, identificado nas colunas da exportação.
- Situações refletem o estado atual; a exportação não reconstrói versões anteriores de cada registro.

## API, limites e operação

`GET /api/dashboard/exportar.zip?periodo=3|6|12|total`, autenticado; período padrão `3`. O site chama o modo paralelo sem mudar a experiência de download. MIME `application/zip`, `Content-Disposition: attachment` e `Cache-Control: no-store`.

São mantidos filtros, cabeçalho fixo, datas e moeda nos quatro arquivos. O limite é de 1.048.575 registros mais o cabeçalho por Excel. Os dados consultados permanecem em memória no processo principal; blocos e XML intermediários consomem espaço temporário em disco. Cada exportação paralela pode criar até quatro processos. Os tempos limite de BFF e Nginx são cinco minutos; não há fila persistente.

O paralelismo não garante ganho para todos os volumes. Em exportações pequenas, iniciar processos pode custar mais do que o trabalho poupado. Não houve mudança de API pública, schema ou migrations para esta reestruturação.

## Plano de medição

1. Usar a mesma imagem Docker, banco, usuário, período e data de referência. Não alterar dados nem iniciar outros testes durante a medição.
2. Executar cinco repetições por modo. Alternar a ordem a cada par para reduzir favorecimento por cache.
3. Medir com `time.time()` desde antes de `run()` até o fim da geração. Registrar também `perf_counter()` para detectar suspensão ou ajuste do relógio.
4. Incluir consultas, preparo de blocos, criação/encerramento de processos, processamento das linhas, montagem dos Excel e ZIP. Excluir transporte HTTP, download e abertura no Excel.
5. Após cada medição, fora do intervalo cronometrado, comparar hashes SHA-256 do XML de todas as células, estilos e estrutura dos workbooks. Timestamps do ZIP não fazem parte da comparação. Qualquer diferença de conteúdo invalida o benchmark.
6. Comparar medianas: `speedup = sequencial / paralelo`; `segundos economizados = sequencial - paralelo`; `redução percentual = 100 × (1 - paralelo / sequencial)`. Valores negativos de economia são relatados como perda, sem alterar expectativas.
7. Preservar JSON de todas as execuções e relatar ambiente, volume e limitações. Uma execução interrompida permanece com status `running` e não é um resultado concluído.

## Como executar

Na raiz do repositório:

```powershell
docker compose build fastapi
New-Item -ItemType Directory -Force tmp/excel-benchmark | Out-Null
$excelBenchmark = Join-Path (Get-Location).Path 'backend-fastapi/scripts/benchmark_excel.py'
$excelResults = Join-Path (Get-Location).Path 'tmp/excel-benchmark'
docker compose run --rm --no-deps --volume "${excelBenchmark}:/app/scripts/benchmark_excel.py:ro" --volume "${excelResults}:/results" fastapi python /app/scripts/benchmark_excel.py --username workmy_carga --reference 2026-10-08 --periods total --repeats 5 --mode compare --workers 4 --batch-size 25000 --output /results/comparacao.json
```

- Somente paralelo: `--mode parallel`.
- Somente sequencial: `--mode sequential`.
- Outros períodos: `--periods 3 6 12 total`.
- `--workers` e `--batch-size` permitem experimentos, mas precisam ser iguais ao relatar uma mesma série de comparação.

O script é somente leitura, exige PostgreSQL explícito e apaga os arquivos exportados após conferi-los. A verificação dos hashes fica fora do cronômetro. O JSON salva progresso a cada execução, contagens, bytes, tempos por etapa, hashes e o resumo de medianas.

## Arquivos e evidências

- Orquestração: `backend-fastapi/src/application/usecases/exportar_dashboard.py`.
- Templates, blocos e montagem: `backend-fastapi/src/infrastructure/documents/dashboard_excel.py`.
- Função executada nos processos: `backend-fastapi/src/infrastructure/documents/excel_rows.py`.
- Benchmark: `backend-fastapi/scripts/benchmark_excel.py`.
- Testes: `test_excel_blocks.py` (equivalência, limites dos blocos, estilos, texto, vazios e falhas) e `test_dashboard_excel.py` (API, autenticação, filtros e isolamento).
- [Relatório da versão por blocos](evidencias/exportacao-excel-paralelo-2026-10-08/RELATORIO.md).

Os relatórios antigos foram preservados. Tempos da versão de workbook único ou de um workbook por processo não devem ser atribuídos à implementação atual.

## Entrega acadêmica de 15/10/2026

A versão atual utiliza diretamente `multiprocessing.Pool`. O benchmark imprime e salva início/fim no fuso America/Sao_Paulo e duração por `time.time()`. O script `backend-fastapi/scripts/demo_paralelismo.ps1` simplifica a execução com `-Mode sequential`, `-Mode parallel` ou `-Mode compare`; salva evidências em `output/pmi-paralelismo/demo`.

[Relatório final, horários, código-fonte e desafios](evidencias/pmi-paralelismo-2026-10-13/RELATORIO_FINAL.md). Essa medição está separada dos históricos anteriores.
