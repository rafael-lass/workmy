# Roteiro de apresentação: WorkMy com multiprocessing

**Apresentação de referência:** `WorkMy_Paralelismo_PMI_15-10-2026_Leonardo.pptx`, 12 slides.  
**Integrantes:** Rafael, Gabriel e Leonardo.  
**Tempo sugerido:** 8 minutos e 50 segundos, incluindo uma demonstração curta. Ensaie com cronômetro: é uma estimativa, não uma duração medida do vídeo.  
**Tema:** otimização da exportação Excel. Este roteiro acompanha a atividade de paralelismo; não substitui a apresentação geral do MVP da N1.

## Preparação

Deixar abertos antes de começar:

1. A apresentação em modo de exibição, conferida no computador que será usado.
2. O dashboard do WorkMy em `http://localhost:5173`, autenticado na conta de dados fictícios `workmy_carga`.
3. Um terminal na pasta `C:\Faculdade\2026\PMI\workmy`.
4. O [relatório técnico](../../docs/evidencias/pmi-paralelismo-2026-10-13/RELATORIO_FINAL.md) e o [JSON do benchmark](../../docs/evidencias/pmi-paralelismo-2026-10-13/comparacao-pool.json), para perguntas.
5. Os arquivos `dashboard_excel.py`, `excel_rows.py` e `benchmark_excel.py` no editor.

Antes da apresentação, se a imagem Docker precisar ser atualizada:

```powershell
cd C:\Faculdade\2026\PMI\workmy
docker compose up -d --build
docker compose ps
```

Fazer essa preparação antes de iniciar o tempo de fala. Não recriar a carga histórica. Não mostrar senha, arquivo `.env` ou credenciais na gravação. Evitar outros benchmarks e downloads enquanto mede. Impedir suspensão do computador durante o ensaio.

## Divisão sugerida

Esta distribuição organiza a apresentação. Ela não afirma quem implementou historicamente cada trecho.

| Pessoa | Conteúdo | Tempo acumulado |
| --- | --- | --- |
| Rafael | Slides 1 a 4: contexto, problema e fluxo | 0:00 a 2:20 |
| Gabriel | Slides 5 a 8: código, medição e resultado | 2:20 a 5:00 |
| Gabriel, com Rafael operando se necessário | Demonstração | 5:00 a 6:20 |
| Leonardo | Slides 9 a 12: dificuldades, limites, testes e conclusão | 6:20 a 8:50 |

## Slide 1: WorkMy — Exportação com multiprocessing

**Quem fala:** Rafael. **Tempo:** 20 segundos.  
**Mostrar:** capa, nome do projeto e integrantes.

**Fala sugerida:**

> Boa noite. Somos Rafael, Gabriel e Leonardo. Vamos apresentar uma melhoria de desempenho no WorkMy, nosso sistema de gestão de clientes, serviços, projetos e pagamentos. Escolhemos a exportação Excel para comparar a execução sequencial com o processamento em paralelo usando a biblioteca multiprocessing do Python.

**Passagem:** “Primeiro, vamos mostrar qual rotina foi escolhida.”

## Slide 2: A rotina escolhida é a exportação Excel

**Quem fala:** Rafael. **Tempo:** 40 segundos.  
**Mostrar:** os quatro tipos de arquivo e o volume de dados. Apontar o nome `ExportarDashboardUseCase.run()`.

**Fala sugerida:**

> O usuário pode exportar seus registros para consultar e analisar fora do sistema. O dashboard entrega um ZIP com quatro arquivos Excel: pagamentos, clientes, serviços e projetos. Cada arquivo tem uma planilha. Para o teste, usamos dados fictícios: duzentos mil pagamentos, doze mil projetos, dez mil clientes e cinquenta e três serviços. O método run coordena as consultas, e o renderer organiza a geração dos arquivos. O repositório já estava clonado na nossa máquina.

**Se perguntarem pelo período:** o site oferece 3, 6 e 12 meses, incluindo o mês atual até hoje, filtrados pelo vencimento dos pagamentos. Os cadastros relacionados acompanham os pagamentos. Total inclui todos os registros da conta. O benchmark apresentado utiliza Total.

## Slide 3: A divisão por arquivo concentrou o trabalho

**Quem fala:** Rafael. **Tempo:** 40 segundos.  
**Mostrar:** primeiro o experimento inicial, depois os oito blocos de pagamentos e onze tarefas.

**Fala sugerida:**

> Na primeira tentativa, cada processo gerava um arquivo inteiro. Isso distribuiu mal o trabalho: pagamentos tinha duzentas mil linhas, enquanto os outros arquivos eram muito menores. Os processos menores terminavam e o maior continuava trabalhando. Nesse experimento histórico, o paralelo levou trinta e oito segundos contra trinta e dois do sequencial. A mudança foi dividir também os pagamentos em blocos de vinte e cinco mil linhas. Assim, temos onze tarefas para distribuir entre quatro processos.

**Precisão importante:** 32,21 s e 38,03 s pertencem ao algoritmo anterior. A comparação principal dos próximos slides usa o mesmo algoritmo por blocos nos dois modos.

## Slide 4: O pool executa blocos independentes

**Quem fala:** Rafael. **Tempo:** 40 segundos.  
**Mostrar:** percorrer as três etapas da esquerda para a direita.

**Fala sugerida:**

> O fluxo tem três etapas. Primeiro, fazemos quatro consultas no banco, dentro de uma visão consistente dos dados, e preparamos os blocos em arquivos temporários. Depois, os workers processam esses blocos. Eles calculam campos, como a indicação de atraso, e convertem as linhas para o formato interno do Excel. Cada worker grava um fragmento próprio. Por fim, o processo principal reúne os fragmentos na ordem original, monta os quatro arquivos e cria o ZIP.

**Precisão importante:** o paralelismo desta versão está no processamento dos blocos. As quatro consultas são sequenciais. O banco não é acessado pelos workers.

**Passagem para Gabriel:** “O Gabriel vai mostrar a diferença entre os dois executores.”

## Slide 5: O sequencial processa um bloco por vez

**Quem fala:** Gabriel. **Tempo:** 30 segundos.  
**Mostrar:** `run_sequential` e a chamada `render_rows(job)`.

**Fala sugerida:**

> Na versão sequencial, percorremos a lista de tarefas e chamamos render_rows para cada bloco. Um bloco termina antes de começar o próximo. Essa função faz o trabalho útil da exportação. Os dados, os formatos e os cálculos são os mesmos usados na versão paralela, o que permite comparar os tempos sem alterar o resultado esperado.

**Se perguntarem se o sequencial foi atrasado:** não há `sleep` nem cálculo artificial para aumentar a duração. O que muda é a forma de executar os mesmos blocos.

## Slide 6: O paralelo usa multiprocessing.Pool

**Quem fala:** Gabriel. **Tempo:** 50 segundos.  
**Mostrar:** `get_context('spawn')`, `Pool(...)`, `processes=min(...)` e `pool.map(...)`.

**Fala sugerida:**

> No paralelo usamos multiprocessing.Pool, com até quatro processos neste teste. O contexto spawn inicia interpretadores separados. O map distribui os jobs e aplica a mesma função render_rows. Como os blocos são independentes, mais de um pode ser processado ao mesmo tempo. O limite também considera a quantidade de tarefas, para não criar processos além do necessário. Cada worker usa seus próprios arquivos temporários. O processo principal espera os resultados e encerra o pool ao sair desse bloco.

**Se perguntarem por que processos:** a serialização das células executa trabalho Python que pode usar vários processos. A medição inclui o custo de criar esses processos. A documentação descreve o Pool como uma forma de distribuir a mesma função entre entradas independentes. [Referência Python](https://docs.python.org/3/library/multiprocessing.html).

**Precisão importante:** quatro CPUs visíveis no Docker não comprovam quatro núcleos físicos exclusivos. Os quatro workers são por exportação.

## Slide 7: Início, fim e duração ficam registrados

**Quem fala:** Gabriel. **Tempo:** 45 segundos.  
**Mostrar:** exemplo de início/fim, primeira linha da tabela e linha de medianas.

**Fala sugerida:**

> Registramos início e fim com time.time e calculamos a diferença em segundos. Também usamos perf_counter como conferência do relógio. Fizemos cinco execuções de cada modo, alternando a ordem. A medição inclui consultas, criação dos processos, processamento e montagem dos arquivos. O download e a abertura no Excel ficam fora. A primeira linha mostra que o sequencial venceu naquela execução. Por isso apresentamos todas as repetições e usamos a mediana, em vez de escolher apenas o melhor resultado.

**Não ler toda a tabela.** Os horários completos dos dois modos estão no relatório. A medição ocorreu em 13/10/2026, com data de referência dos dados fixada em 08/10/2026.

## Slide 8: A mediana paralela reduz o tempo em 18,2%

**Quem fala:** Gabriel. **Tempo:** 35 segundos.  
**Mostrar:** barras, 15,57 s, 12,75 s e economia de 2,83 s.

**Fala sugerida:**

> A mediana sequencial ficou em quinze vírgula cinquenta e sete segundos. Com o pool, ficou em doze vírgula setenta e cinco. A diferença entre as medianas foi de aproximadamente dois vírgula oitenta e três segundos, ou dezoito vírgula dois por cento de redução no tempo. O speedup foi de um vírgula vinte e dois. Esse resultado vale para este ambiente e esse volume de dados. Agora vamos mostrar como executamos a comparação.

**Se perguntarem pelo cálculo:**

```text
Economia = mediana sequencial − mediana paralela
Redução (%) = 100 × (1 − mediana paralela / mediana sequencial)
Speedup = mediana sequencial / mediana paralela
```

Usar os valores completos do JSON no cálculo. A diferença dos valores arredondados do slide pode variar em um centésimo.

## Demonstração depois do slide 8

**Quem fala:** Gabriel. **Tempo reservado:** 1 minuto e 20 segundos.  
**Quem pode operar:** Rafael, seguindo os comandos combinados.  
**Objetivo:** mostrar o recurso e a execução real, sem prometer que uma única repetição repetirá a mediana.

### 1. Mostrar o dashboard por alguns segundos

Apontar a área **Exportar planilhas Excel** e selecionar **Total**.

> Esta é a função no site. O usuário escolhe o período e recebe os quatro arquivos num ZIP. A rota web está configurada para usar o modo paralelo.

Não iniciar um download ao mesmo tempo que o benchmark, pois as duas exportações disputariam recursos. Se quiser mostrar os arquivos, deixar um pacote já exportado antes do início da apresentação, identificado como exemplo preparado.

### 2. Executar uma comparação curta no terminal

```powershell
cd C:\Faculdade\2026\PMI\workmy
powershell -NoProfile -ExecutionPolicy Bypass -File .\backend-fastapi\scripts\demo_paralelismo.ps1 -Mode compare -Repeats 1 -Workers 4
```

> Este script chama o mesmo caso de uso da exportação nos dois modos. Ele mostra início, fim e duração, confere o conteúdo dos arquivos e salva as evidências em JSON. Neste ensaio ao vivo estamos fazendo uma repetição por modo. A tabela dos slides vem da série anterior de cinco repetições.

Apontar as linhas `INÍCIO`, `FIM`, `TEMPO`, `CONFERÊNCIA` e `RESULTADO`. A inicialização do comando Docker pode fazer a demonstração demorar mais que a duração cronometrada da exportação.

### 3. Comentar o resultado observado

**Se o paralelo vencer:**

> Nesta execução, o sequencial levou [ler o valor] segundos e o paralelo levou [ler o valor]. A diferença desta execução foi [ler a economia] segundos. O resultado é mais uma observação, separada da série apresentada.

**Se o paralelo perder:**

> Nesta execução, o paralelo demorou mais. Abrir os processos tem custo, e a carga da máquina varia. Isso também aconteceu em um ensaio anterior e ficou registrado. A conclusão dos slides se refere à mediana de cinco repetições, não a uma garantia de vitória em toda execução.

**Se houver falha do ambiente ou demora além do tempo reservado:**

> A execução ao vivo não foi concluída dentro do tempo reservado. Vamos usar o relatório previamente medido para explicar o resultado. Não vamos apresentar esta tentativa como aprovada.

Retomar os slides. Não executar cinco repetições durante uma apresentação curta. Não insistir em várias tentativas até obter um resultado favorável.

**Passagem para Leonardo:** “A Leonardo vai explicar as dificuldades, os testes e os limites dessa melhoria.”

## Slide 9: Dificuldades encontradas na implementação

**Quem fala:** Leonardo. **Tempo:** 40 segundos.  
**Mostrar:** distribuição desigual e preservação dos arquivos; depois, custo de processos e ambiente.

**Fala sugerida:**

> A primeira dificuldade foi distribuir o volume de pagamentos entre os processos. Também tivemos de considerar o custo de iniciar workers e preparar as entradas. Outro cuidado foi preservar o resultado do Excel: ordem das linhas, textos, datas e valores monetários. Usamos testes de equivalência e hashes para comparar os arquivos. O ambiente também afetou ensaios anteriores, com restrições de temporários e divergência entre relógios. Por isso registramos as condições e preservamos as tentativas anteriores.

## Slide 10: Deadlocks, concorrência e escalabilidade

**Quem fala:** Leonardo. **Tempo:** 55 segundos.  
**Mostrar:** os quatro tópicos, sem ler os parágrafos por completo.

**Fala sugerida:**

> Não observamos deadlocks nos testes executados. Cada worker grava um fragmento separado, e apenas o processo principal monta o Excel. Isso reduz a disputa por recursos compartilhados. Ainda assim, não testamos todos os tipos de travamento. Cada exportação pode abrir quatro processos e ainda não existe um limite global de exportações simultâneas. Os dados também ocupam memória e os temporários usam disco. O ganho não é linear porque consultas, preparação e montagem continuam sequenciais, além do custo de iniciar o pool. Mais processos, portanto, precisam ser avaliados por medição.

**Se perguntarem o que é deadlock:** é uma situação de espera circular por recursos, em que os envolvidos não conseguem avançar. Um processo simplesmente lento ou preso em uma operação não é, por si só, prova de deadlock.

**Próximo passo concreto:** limitar trabalhos simultâneos, estabelecer prazo do processamento e medir memória e disco antes de ampliar a configuração.

## Slide 11: A comparação preservou o conteúdo

**Quem fala:** Leonardo. **Tempo:** 35 segundos.  
**Mostrar:** 11 testes históricos, integridade e limites.

**Fala sugerida:**

> A evidência original da exportação contém onze testes aprovados. Eles verificam acesso, períodos, isolamento de usuário, ordem das linhas, formatação e limpeza quando ocorre uma exceção tratada no worker. Os hashes das partes verificadas dos quatro arquivos foram iguais nas dez execuções do benchmark. O benchmark usou PostgreSQL real, enquanto os testes de API usam SQLite isolado. Não medimos várias exportações simultâneas nem o pico de recursos.

**Informação adicional para perguntas:** na revisão de 13/10, a suíte completa passou com **71 testes backend e 23 frontend**, além de lint e build. Quatro testes de carga histórica ficaram ignorados por falta de PostgreSQL descartável. Os 11 do slide são o recorte histórico da exportação, incluído na suíte backend, e não devem ser somados novamente aos 94 aprovados.

**Precisão importante:** “conteúdo igual” significa igualdade das partes XML de workbook, estilos e células comparadas. Não significa igualdade byte a byte do ZIP inteiro nem abertura visual comprovada no Excel.

## Slide 12: O pool distribui o trabalho dos pagamentos

**Quem fala:** Leonardo. **Tempo:** 20 segundos.  
**Mostrar:** resultado final e concluir olhando para o público.

**Fala sugerida:**

> A divisão em blocos permitiu distribuir o maior conjunto de dados entre os processos. Neste ensaio, a mediana caiu de quinze vírgula cinquenta e sete para doze vírgula setenta e cinco segundos, preservando o conteúdo verificado. O próximo passo é controlar exportações simultâneas e medir recursos para evoluir com segurança. Obrigada.

## Consulta rápida para perguntas

| Pergunta | Resposta curta |
| --- | --- |
| O que foi paralelizado? | Cálculo de campos e serialização das linhas dos blocos para XML do Excel |
| O PostgreSQL está paralelo nessa função? | A aplicação faz quatro consultas sequenciais, no mesmo snapshot; os workers processam dados já lidos |
| São onze processos? | São onze tarefas e até quatro workers; um worker pode executar mais de uma tarefa |
| Cada worker gera um Excel? | Na versão atual, gera fragmentos de linhas; o processo principal monta os quatro XLSX |
| Por que 25 mil linhas por bloco? | É a configuração testada. Não foi provado que seja o tamanho ótimo |
| Por que quatro workers? | Era a configuração usada com quatro CPUs visíveis no Docker. Não há prova de que quatro seja ideal em toda máquina |
| Por que o ganho não foi quatro vezes maior? | Parte do fluxo continua sequencial e existe custo de processos, I/O e montagem |
| O paralelo sempre ganha? | Não. Perdeu em uma das cinco repetições e em um ensaio isolado registrado |
| O site ficou 18,2% mais rápido? | O tempo mediano de consulta e geração caiu 18,2% no ensaio. O benchmark não mede a experiência HTTP completa |
| Como sabemos que o arquivo está correto? | Testes de valores/formatação/ordem e comparação das partes XML selecionadas, com hashes iguais entre modos |
| O sistema suporta muitos usuários exportando juntos? | A capacidade ainda não foi medida. Falta limite global e teste de concorrência |
| O que acontece se um worker falhar? | Exceções comuns são propagadas e o teste verifica limpeza. Travamento e morte abrupta ainda precisam de tratamento e testes específicos |

## Glossário para a fala

| Termo | Explicação simples |
| --- | --- |
| CPU | Unidade de processamento do computador |
| Processo / worker | Programa em execução que recebe uma parte do trabalho |
| Pool | Grupo de processos que executam tarefas distribuídas |
| Job | Uma tarefa, neste caso um bloco de registros |
| Spawn | Modo de iniciar um novo interpretador Python para cada processo |
| Map | Aplica uma função a cada item de uma lista de tarefas |
| Snapshot | Visão consistente do banco durante a leitura |
| XML / OOXML | Formato interno que representa o conteúdo e a estrutura das planilhas |
| XLSX | Formato do arquivo Excel exportado |
| ZIP | Pacote que reúne os quatro arquivos Excel |
| Hash SHA-256 | Resumo digital usado para comparar se o conteúdo verificado mudou |
| Mediana | Valor central depois de ordenar os tempos medidos |
| Speedup | Razão entre o tempo sequencial e o paralelo |
| I/O | Operações de entrada e saída, como leitura e gravação em disco |
| Deadlock | Espera circular por recursos que impede o avanço dos envolvidos |

## Localização dos arquivos para a demonstração

| O que localizar | Arquivo |
| --- | --- |
| Funções sequencial e paralela | [dashboard_excel.py](/C:/Faculdade/2026/PMI/workmy/backend-fastapi/src/infrastructure/documents/dashboard_excel.py:19) |
| Trabalho de cada bloco | [excel_rows.py](/C:/Faculdade/2026/PMI/workmy/backend-fastapi/src/infrastructure/documents/excel_rows.py:48) |
| Orquestração pelo método run | [exportar_dashboard.py](/C:/Faculdade/2026/PMI/workmy/backend-fastapi/src/application/usecases/exportar_dashboard.py:13) |
| Consultas do banco | [postgres_excel_query.py](/C:/Faculdade/2026/PMI/workmy/backend-fastapi/src/infrastructure/persistence/repositories/postgres_excel_query.py) |
| Início, fim e conferência | [benchmark_excel.py](/C:/Faculdade/2026/PMI/workmy/backend-fastapi/scripts/benchmark_excel.py:63) |
| Comando da demonstração | [demo_paralelismo.ps1](/C:/Faculdade/2026/PMI/workmy/backend-fastapi/scripts/demo_paralelismo.ps1) |
| Números originais dos slides | [comparacao-pool.json](../../docs/evidencias/pmi-paralelismo-2026-10-13/comparacao-pool.json) |
| Melhorias encontradas na revisão | [Revisão crítica](REVISAO_CRITICA.md) |

Para repetir a série completa fora do tempo da apresentação:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\backend-fastapi\scripts\demo_paralelismo.ps1 -Mode compare -Repeats 5 -Workers 4
```

Esse comando gera uma evidência nova. Preservar os arquivos anteriores e identificar os resultados de cada série separadamente.
