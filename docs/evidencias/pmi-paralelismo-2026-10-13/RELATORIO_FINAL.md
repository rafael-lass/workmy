# WorkMy: paralelização da exportação Excel

Trabalho PMI / ADS. Apresentação prevista para 15/10/2026. Medição registrada em 13/10/2026. Integrantes: Rafael, Gabriel e Leonardo.

## 1. Repositório e rotina escolhida

O repositório já estava clonado em `C:/Faculdade/2026/PMI/workmy`, com remote `git@github.com:rafael-lass/workmy.git`. Não foi necessário clonar novamente. A base Git é `6a97132e56da6fdc48e0e76894661251fa779639`, com alterações locais. [Hashes dos arquivos desta versão](versao.json).

A rotina é a exportação financeira/cadastral acessível no dashboard. `ExportarDashboardUseCase.run()` consulta a conta autenticada e chama `DashboardExcelRenderer.render()`. O produto é um ZIP contendo Pagamentos, Clientes, Serviços e Projetos em quatro arquivos XLSX, com uma aba em cada arquivo. O teste usa período Total e a conta fictícia `workmy_carga`.

### Análise de desempenho

A tentativa inicial destinava um workbook a cada processo. A planilha de 200.000 pagamentos concentrava o trabalho, enquanto os demais workers terminavam os cadastros pequenos. Essa experiência teve mediana de 32,209 s sequencial e 38,026 s paralela em 08/10/2026, ou seja, o paralelo piorou. Essa comparação histórica usa um algoritmo diferente da versão atual e não entra nos resultados abaixo.

A melhoria divide as linhas em blocos de 25.000 registros, incluindo os pagamentos. São oito blocos de pagamentos e um bloco para cada um dos três cadastros: onze tarefas para um pool de quatro workers. Cada tarefa calcula atraso, traduz etapas e converte as células para o XML de uma planilha XLSX.

## 2. Implementação

A biblioteca utilizada é `multiprocessing`, por `get_context('spawn').Pool`. Os processos recebem caminhos para blocos privados gravados em disco. Conexões de banco, sessões SQLAlchemy e workbooks não são compartilhados. Os quatro workers correspondem às quatro CPUs visíveis no Docker da medição.

A leitura é a mesma nos dois modos: quatro projeções SQL numa transação REPEATABLE READ. O sequencial e o paralelo usam os mesmos blocos, cálculos e formatos. Não há atraso artificial nem operação descartável para aumentar o tempo sequencial. Só muda o executor das tarefas.

### Código-fonte sequencial real

Trecho de `backend-fastapi/src/infrastructure/documents/dashboard_excel.py`:

```python
def run_sequential(jobs):
    """Executa a mesma tarefa em um único processo, um bloco após o outro."""
    return [render_rows(job) for job in jobs]
```

### Código-fonte paralelo real

O mesmo arquivo importa `get_context` de `multiprocessing`:

```python
from multiprocessing import get_context

def run_parallel(jobs, workers):
    """Pool de processos reais da biblioteca multiprocessing."""
    if not jobs:
        return []
    with get_context('spawn').Pool(processes=min(workers, len(jobs))) as pool:
        return pool.map(render_rows, jobs)
```

### Função compartilhada pelos modos

Código de `backend-fastapi/src/infrastructure/documents/excel_rows.py`:

```python
def render_rows(job):
    """Mesma tarefa para sequential e ProcessPoolExecutor; apenas arquivos privados."""
    source, destination, key, columns, offset, today, money_style, date_style = job
    started = perf_counter()
    # O pickle é produzido nesta exportação, em diretório privado, nunca pelo usuário.
    with open(source, 'rb') as stream:
        rows = pickle.load(stream)
    with open(destination, 'w', encoding='utf-8', newline='') as stream:
        for row_number, original in enumerate(rows, offset + 2):
            row = original.copy()
            if key == 'pagamentos':
                row['atrasado'] = row['status'] == 'PENDENTE' and row['data_vencimento'] < today
            elif key == 'projetos':
                row['status'] = STAGES.get(row['status'], row['status'])
            elif key == 'servicos':
                document = row.get('descricao_documento')
                row['descricao'] = plain_text(document.get('doc')) if document else row.get('descricao')
            cells = ''.join(cell_xml(f'{letter}{row_number}', row.get(field), money_style, date_style)
                            for field, letter in columns)
            stream.write(f'<row r="{row_number}">{cells}</row>')
    return {'rows': len(rows), 'seconds': perf_counter() - started}
```

A chamada escolhe `run_parallel(jobs, self.workers)` quando o modo é `parallel` e `run_sequential(jobs)` quando é `sequential`. O programa de benchmark usa o guard `if __name__ == '__main__'` e `asyncio.run(...)`, para executar corretamente com spawn.

### Início, fim e duração

`benchmark_excel.py` registra `started_at` e `finished_at`, incluindo fuso `-03:00`, e os valores numéricos `started_epoch` e `finished_epoch`. A duração é `finished_epoch - started_epoch`, obtida com `time.time()`. `perf_counter()` serve como controle independente contra suspensão do computador ou ajuste do relógio. O período de dados permanece fixo em 08/10/2026, embora os horários reais de execução sejam de 13/10/2026.

## 3. Tempos antes e depois

A comparação justa é entre os executores da mesma implementação por blocos, com o mesmo volume e cinco repetições por modo. O script alterna a ordem a cada par.

| Repetição | Modo | Início (São Paulo) | Fim (São Paulo) | Duração |
| --- | --- | --- | --- | ---: |
| 1 | sequential | 2026-10-13T17:02:11.605-03:00 | 2026-10-13T17:02:22.759-03:00 | 11.154 s |
| 1 | parallel | 2026-10-13T17:02:23.128-03:00 | 2026-10-13T17:02:36.797-03:00 | 13.669 s |
| 2 | parallel | 2026-10-13T17:02:37.215-03:00 | 2026-10-13T17:02:51.754-03:00 | 14.539 s |
| 2 | sequential | 2026-10-13T17:02:52.219-03:00 | 2026-10-13T17:03:08.986-03:00 | 16.768 s |
| 3 | sequential | 2026-10-13T17:03:09.347-03:00 | 2026-10-13T17:03:23.640-03:00 | 14.293 s |
| 3 | parallel | 2026-10-13T17:03:24.025-03:00 | 2026-10-13T17:03:36.773-03:00 | 12.748 s |
| 4 | parallel | 2026-10-13T17:03:37.271-03:00 | 2026-10-13T17:03:49.821-03:00 | 12.550 s |
| 4 | sequential | 2026-10-13T17:03:50.315-03:00 | 2026-10-13T17:04:05.890-03:00 | 15.575 s |
| 5 | sequential | 2026-10-13T17:04:06.441-03:00 | 2026-10-13T17:04:22.913-03:00 | 16.472 s |
| 5 | parallel | 2026-10-13T17:04:23.482-03:00 | 2026-10-13T17:04:36.018-03:00 | 12.535 s |

| Medida | Resultado |
| --- | ---: |
| Mediana sequencial | 15.575 s |
| Mediana paralela | 12.748 s |
| Economia de tempo | 2.827 s |
| Redução percentual | 18.15% |
| Speedup (sequencial / paralelo) | 1.222× |

A mediana do processamento dos blocos foi 7.739 s no sequencial e 5.458 s no paralelo. Medianas de etapas não precisam somar a mediana do total.

### Ambiente e critério de integridade

Python 3.12.15 no Docker Linux/WSL2, PostgreSQL 15, quatro CPUs visíveis, quatro workers e blocos de 25.000 linhas. Conta fictícia com 200.000 pagamentos, 12.000 projetos, 10.000 clientes e 53 serviços. O banco não recebeu gravações durante o benchmark.

Cada tempo inclui consultas, temporários, abertura/encerramento do pool, cálculos/serialização, montagem XLSX e ZIP. Não inclui download HTTP, abertura no Excel nem a comparação de hashes, que ocorre após o cronômetro. Compara-se SHA-256 do XML das células, estilos e estrutura dos quatro workbooks, ignorando timestamps do pacote. Todos os hashes foram iguais nas dez execuções.

A máquina executa outros processos normais e o tempo variou entre repetições. Esta série demonstra ganho neste ambiente, sem garantir o mesmo resultado em qualquer computador ou volume. Não houve estudo estatístico com intervalo de confiança nem isolamento físico da CPU.

## 4. Dificuldades encontradas

- **Divisão inicial desbalanceada:** um workbook por processo manteve quase todo o custo em Pagamentos. A divisão em blocos distribuiu o maior conjunto.
- **Custo de processos e transporte:** iniciar workers e transportar listas grandes acrescenta tempo. Os jobs referenciam arquivos privados de blocos, com caminhos e metadados pequenos.
- **Estrutura XLSX:** a reunião dos blocos precisa preservar linhas, estilos de moeda/data, caracteres especiais e cabeçalhos. Templates XlsxWriter, offsets determinísticos e testes de equivalência validam isso.
- **Ambiente de execução:** chamadas anteriores tiveram bloqueio de temporários/permissões no Windows e uma medição interrompida apresentou divergência entre relógios. Temporários locais nos testes, execução Docker e verificação time.time/perf_counter tornam o problema identificável.
- **Experimento de banco concorrente:** importar snapshots PostgreSQL exigia sessões independentes e contrato consistente de chaves. Essa versão experimental foi substituída pela leitura simples, igual nos dois modos, concentrando o pool na tarefa de CPU medida.

## 5. Desafios exigidos pelo trabalho

### Deadlocks

Nenhum deadlock foi observado nas execuções e testes registrados. Os workers não disputam locks da aplicação, conexões ou um workbook compartilhado. Cada bloco tem entrada/saída distinta; o processo principal aguarda `pool.map` e só depois reúne os arquivos. `with Pool(...)` encerra o pool e falhas chegam ao chamador. Isso reduz pontos de disputa, mas não prova impossibilidade de bloqueio: falhas de I/O, falta de recursos ou worker preso ainda exigem monitoramento/timeout numa evolução. Os limites HTTP de cinco minutos não são um mecanismo de cancelamento automático do pool.

### Concorrência

Processos escrevem fragmentos exclusivos, num diretório temporário exclusivo por exportação. O processo principal é o único que monta XLSX e ZIP e segue offsets da ordem original. O banco fornece uma visão consistente por REPEATABLE READ. A falha de um worker impede a entrega parcial e a limpeza remove os temporários. Os hashes iguais verificam a integridade dos arquivos neste conjunto de dados.

### Escalabilidade

O pool possui até quatro processos, limitado pelo número de jobs. Mais workers não significam ganho linear: a leitura, o preparo de blocos e a compactação final continuam sequenciais. A lista consultada ocupa memória e os intermediários usam disco. Exportações simultâneas podem multiplicar processos e consumo de recursos. Não foram medidos pico de memória/disco nem várias exportações simultâneas. Evoluções possíveis: fila de tarefas, limite global de concorrência, leitura incremental e estudo de tamanhos de bloco/workers.

### Ganho sequencial versus paralelo

A redução de 18.2% no total é menor que o ganho isolado na etapa paralelizável. Parte do trabalho permanece serial e há custo de iniciar processos. Em volumes pequenos, o paralelo pode ser mais lento. O ensaio ao vivo mede uma única execução e pode apresentar valores diferentes da mediana de cinco repetições. A apresentação mantém os números medidos e não promete um ganho universal.

## 6. Testes e evidências

- [Benchmark com horários e resultados](comparacao-pool.json): status completo, cinco execuções por modo e conteúdo idêntico.
- [JUnit](testes.xml): 11 aprovados, zero falhas, em 8,95 s. API em SQLite isolado; pool real nos testes de blocos. O benchmark usa PostgreSQL real do Compose.
- Cobertura: autenticado/anônimo, isolamento de usuário, períodos, virada de ano, Total e cadastros sem pagamentos, arquivos vazios, ordem entre blocos, texto literal, datas/moedas, falha de worker e limpeza.
- Fonte completa: `dashboard_excel.py`, `excel_rows.py`, `exportar_dashboard.py`, `benchmark_excel.py` e `demo_paralelismo.ps1`.
- Históricos anteriores permanecem preservados no diretório de 08/10/2026. Não se atribui à versão Pool o resultado de outro executor.

## 7. Atendimento ao enunciado

| Item | Evidência |
| --- | --- |
| 1a: repositório clonado | Worktree Git existente e remote conferido |
| 1b: análise de oportunidade | Desbalanceamento de Pagamentos e histórico do experimento inicial |
| 1c: início/fim e tempo | started_at, finished_at e time.time no JSON |
| 1d: multiprocessing e pool | get_context('spawn').Pool, quatro workers, fonte real |
| 2a: dificuldades | Seção 4 |
| 2b: antes e depois | Cinco pares, medianas, economia e speedup |
| 2c: fonte sequencial/paralela | Funções reais e worker compartilhado reproduzidos acima |
| 2d: deadlocks/concorrência/escala/ganho | Seção 5, distinguindo observações e limites não testados |

O exemplo do Classroom não foi fornecido nesta conversa e não há afirmação de que foi consultado. A implementação atende ao enunciado fornecido, usando Python e a biblioteca padrão multiprocessing.

## Ensaio ao vivo e variação

O comando `demo_paralelismo.ps1 -Mode compare -Repeats 1` foi ensaiado em 13/10/2026. Uma execução sequencial levou 11,815 s e a paralela 12,616 s, com conteúdo idêntico. Nesse ensaio o pool foi 0,801 s mais lento. A evidência permanece em `output/pmi-paralelismo/demo/compare-20261013-170632-241.json`. Esse par isolado não integra a série principal nem substitui sua mediana. Na demonstração, relatar o valor observado mesmo quando ele não repete o ganho da série.

Os comandos individuais `-Mode sequential` e `-Mode parallel` também foram executados e produziram relatórios completos. [Evidência do ensaio](ensaio-demo.json). Os arquivos de dados do banco não foram alterados.
