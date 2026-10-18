# Relatório de performance — exportação em blocos

Data: 08/10/2026. Base Git `6a97132e56da6fdc48e0e76894661251fa779639`, com alterações locais. Os hashes dos arquivos implementados estão em [versao-blocos.json](versao-blocos.json).

## Resultado comprovado

Na mesma implementação, a mediana caiu de **12.05 s no sequencial para 10.04 s com multiprocessing**: economia de **2.01 s**, redução de **16.7%** no tempo e fator de aceleração **1.20×**.

Foram cinco execuções de cada modo, alternando a ordem de execução por par. O sequencial não possui atrasos artificiais e executa a mesma função de processamento dos mesmos blocos. Os quatro workbooks tiveram conteúdo idêntico em todas as dez execuções, conferido por SHA-256 do XML de células, estilos e estrutura. Metadados de horário do ZIP são ignorados.

| Repetição | Sequencial | Multiprocessing |
| --- | ---: | ---: |
| 1 | 10.734 s | 10.335 s |
| 2 | 13.159 s | 9.926 s |
| 3 | 11.992 s | 8.975 s |
| 4 | 12.573 s | 11.070 s |
| 5 | 12.050 s | 10.036 s |
| **Mediana** | **12.050 s** | **10.036 s** |

Evidência: [blocos-comparacao.json](blocos-comparacao.json). O teste inicial ficou separado em [blocos-piloto.json](blocos-piloto.json) e não participa dessas medianas.

## Ambiente e volume

- Python 3.12.15, PostgreSQL 15 do Docker Compose, plataforma `Linux-6.6.114.1-microsoft-standard-WSL2-x86_64-with-glibc2.41`.
- 4 CPUs visíveis no container, até quatro workers e blocos de 25 mil registros.
- Conta fictícia `workmy_carga`, referência 08/10/2026, período Total.
- 200.000 pagamentos, 12.000 projetos, 10.000 clientes e 53 serviços.
- Oito blocos de pagamentos e um bloco de cada cadastro: onze tarefas independentes.
- ZIP final de aproximadamente 18,37 MB, com quatro XLSX e sem dashboard.

## O que mudou e por que funcionou

A versão anterior entregava um workbook inteiro a cada processo. A planilha de pagamentos concentrava a maior parte do custo e continuava sendo executada por um único processo. Nesta versão, o trabalho grande também é dividido: cada worker converte e serializa um bloco de linhas; o processo principal reúne os fragmentos na ordem original, aplica a estrutura do template XLSX e gera os arquivos finais.

A leitura do banco é igual nos dois modos: quatro projeções em uma transação consistente. Cada worker recebe caminhos de arquivos temporários privados, sem sessão SQLAlchemy ou conexão. O transporte dos 200 mil registros pela fila de multiprocessing foi substituído por tarefas pequenas que referenciam os blocos em disco.

Mediana da etapa de processamento de blocos: **5.206 s → 3.037 s**. Leitura do banco, preparação de blocos e montagem final continuam contribuindo para o tempo total; por isso o ganho geral é menor que o ganho nessa etapa.

## Cronometragem e integridade

`time.time()` mede o pipeline desde antes de `run()` até a obtenção do ZIP. Inclui leitura, temporários, criação e encerramento dos processos, montagem dos Excel e empacotamento. A conferência dos hashes ocorre depois do cronômetro. `perf_counter()` registra etapas e serve como checagem independente contra suspensão ou ajuste do relógio.

A comparação usa a mesma implementação para ambos os modos. Consultas, formatos, ordenação e compressão não são simplificados somente no paralelo. Nenhum dado de negócio foi gravado durante o benchmark.

## Testes e validação no site

- **11 testes aprovados**, zero falhas: [JUnit](testes-blocos.xml). Cobrem equivalência sequencial/paralela em limites de blocos, ordem, datas, moeda, texto literal, arquivos vazios, falha em worker e limpeza; API com autenticação, isolamento, períodos e Total.
- Comando: `.venv/Scripts/python.exe -m pytest tests/integration/test_excel_blocks.py tests/integration/test_dashboard_excel.py -q --basetemp=../tmp/pytest-excel-final --junitxml=../docs/evidencias/exportacao-excel-paralelo-2026-10-08/testes-blocos.xml -o faulthandler_timeout=30`.
- Testes locais: Python 3.13.13, SQLite isolado para a API e processos reais nos testes dos blocos. O benchmark utilizou PostgreSQL real do Compose.
- Docker do site atualizado; modo paralelo por blocos é o padrão.
- Download real via Nginx → BFF → API: **HTTP 200**, MIME `application/zip`, **9,61 s** e 18.366.101 bytes. Essa chamada isolada não integra as medianas: [http-blocos.json](http-blocos.json).
- O download foi lido inteiramente com Openpyxl: 200.000 linhas de pagamentos, 10.000 clientes, 53 serviços e 12.000 projetos. Conteúdo corresponde ao benchmark: [download-blocos-validado.json](download-blocos-validado.json).

## Limitações e evidências anteriores

Este ganho foi medido neste ambiente e volume. Exportações pequenas podem ficar mais lentas ao iniciar processos; não existe promessa de ganho universal. Não foram medidos pico de memória, ocupação máxima de disco temporário ou várias exportações simultâneas. Os dados continuam materializados no processo principal e os blocos usam disco temporário. Não houve validação em Microsoft Excel instalado; houve leitura completa com Openpyxl e testes de estrutura/conteúdo.

Os arquivos de experiências anteriores permanecem preservados. `comparacao-apenas-renderizacao.json` corresponde ao algoritmo anterior, com um workbook por processo. `validacao-paralelo-postgres.json` foi interrompido e apresenta divergência grande entre relógios; não é evidência válida de velocidade. Nenhum desses resultados entra nas medianas desta versão.

Para repetir a comparação ou chamar somente o modo paralelo, consulte [plano e comandos](../../EXPORTACAO_EXCEL.md).
