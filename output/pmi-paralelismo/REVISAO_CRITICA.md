# Revisão crítica do WorkMy: exportação e apresentação

**Data:** 13/10/2026, horário de São Paulo. **Escopo:** exportação Excel, execução sequencial e com multiprocessing, benchmark, integração web, evidências e apresentação de 12 slides. Esta revisão não é uma auditoria completa de segurança de todos os módulos do WorkMy.

## Parecer

A implementação permite uma comparação válida entre os dois executores: ambos usam os mesmos dados, blocos, cálculos e formatos. Não encontrei atraso artificial para prejudicar o sequencial. Os números apresentados correspondem ao JSON de evidências: mediana de **15,5748 s** no sequencial e **12,7477 s** no paralelo, redução de **18,15%** e speedup de **1,22×**.

A apresentação cobre os itens da atividade de paralelismo registrados no relatório anterior. Está adequada para explicar um experimento acadêmico, desde que a fala preserve os limites da medição. A implementação ainda precisa de controles de recursos e recuperação de falhas antes de sustentar exportações simultâneas em escala.

Os slides atuais não constituem, sozinhos, a apresentação completa do MVP da N1. Os requisitos dessa entrega anterior são mais amplos. A comparação entre as duas entregas está abaixo.

## 1. Melhorias no código, por prioridade

As situações de sobrecarga e travamento abaixo são riscos identificados por leitura do código. Não executei um teste de saturação nem provoquei interrupção abrupta dos serviços.

### Alta: limitar exportações simultâneas no servidor

**Local:** [criação do renderer na rota](/C:/Faculdade/2026/PMI/workmy/backend-fastapi/src/presentation/rest/dashboard.py:31) e [abertura do pool](/C:/Faculdade/2026/PMI/workmy/backend-fastapi/src/infrastructure/documents/dashboard_excel.py:28).

Cada requisição cria um renderer e seu próprio pool de até quatro processos. O bloqueio do botão evita cliques repetidos apenas naquela instância da interface. Outras abas, usuários ou chamadas diretas continuam podendo exportar ao mesmo tempo. Por exemplo, cinco exportações grandes podem criar até vinte workers, além dos processos do servidor, disputando a mesma CPU e memória.

**Proposta:** aplicar um limite de trabalhos ativos antes de consultar os dados, com resposta de fila/ocupado e limite por usuário. Em implantação com várias instâncias, o limite precisa ser compartilhado. Medir duas e quatro exportações simultâneas antes de definir capacidade. Uma fila de tarefas persistente é uma evolução posterior, não uma exigência para demonstrar o trabalho.

### Alta: estabelecer prazo de execução e encerramento dos workers

**Local:** [espera em pool.map](/C:/Faculdade/2026/PMI/workmy/backend-fastapi/src/infrastructure/documents/dashboard_excel.py:29).

`pool.map()` aguarda os resultados sem prazo configurado. Uma exceção Python normal é diferente de um worker que trava ou morre abruptamente. O teste atual cobre uma exceção por valor inválido, não todas essas formas de falha. O timeout de cinco minutos no proxy não implementa cancelamento cooperativo do processamento da exportação.

**Proposta:** definir um prazo total do trabalho, encerrar e aguardar o pool após expiração, registrar o motivo e remover os temporários. Uma opção a avaliar é `map_async(...).get(timeout=...)`, com tratamento explícito do timeout e da finalização. Acrescentar testes isolados de worker preso, término abrupto e limpeza. A documentação distingue a espera bloqueante de `map` e a espera com timeout de `AsyncResult.get`. [Documentação Python](https://docs.python.org/3/library/multiprocessing.html#module-multiprocessing.pool).

### Média: reduzir o pico de memória ao consultar e entregar

**Locais:** [materialização da consulta](/C:/Faculdade/2026/PMI/workmy/backend-fastapi/src/infrastructure/persistence/repositories/postgres_excel_query.py:30), [acúmulo dos conjuntos](/C:/Faculdade/2026/PMI/workmy/backend-fastapi/src/application/usecases/exportar_dashboard.py:21) e [buffer do BFF](/C:/Faculdade/2026/PMI/workmy/frontend/bff/server.js:108).

Todos os registros são convertidos em listas de dicionários antes da geração. Depois, os blocos são gravados em disco. Portanto, dividir a serialização em blocos não torna a leitura incremental. Na entrega, o BFF acumula os chunks e usa `Buffer.concat`, mantendo o ZIP inteiro em memória antes de responder. O navegador também recebe um Blob completo.

**Proposta:** medir pico de memória e espaço temporário; preparar os blocos com leitura incremental mantendo a consistência e a ordenação; transmitir a resposta binária pelo BFF com tratamento de desconexão e backpressure. Preservar a renovação de sessão antes de enviar cabeçalhos. O Node expõe respostas HTTP como streams. [Documentação Node.js](https://nodejs.org/api/http.html#class-httpincomingmessage).

### Média: tratar limites e erros como parte da experiência do produto

**Local:** [limite de linhas](/C:/Faculdade/2026/PMI/workmy/backend-fastapi/src/infrastructure/documents/dashboard_excel.py:127).

O renderer rejeita mais de 1.048.575 registros por planilha, mas isso ocorre depois de carregar as listas. A rota não converte esse `ValueError` em um erro específico da exportação. No caminho inspecionado, o usuário tende a receber um erro genérico, sem orientação sobre reduzir o período.

**Proposta:** usar exceção específica para limite excedido, tratá-la na API e explicar qual período selecionar. Validar volume antes de alocar todo o conjunto quando for viável. Testar o erro sem criar um milhão de registros reais.

### Média: escolher o executor conforme o volume e os recursos

**Local:** [modo padrão do caso de uso](/C:/Faculdade/2026/PMI/workmy/backend-fastapi/src/application/usecases/exportar_dashboard.py:13).

O modo web é sempre paralelo, inclusive para conjuntos pequenos. Isso atende à escolha anterior de deixar o paralelo como padrão, mas não comprova que seja a configuração mais rápida em todos os casos. Quatro workers são uma configuração fixa, não uma adaptação ao limite de CPU de qualquer implantação.

**Proposta futura:** medir volumes pequenos, médios e grandes com 1, 2 e 4 workers, mantendo modos forçados no benchmark. Somente depois adotar um limiar automático no site. `spawn` inicia interpretadores novos, e esse custo deve continuar dentro da medição. [Documentação Python](https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods).

### Média: isolar e testar melhor a montagem manual de XLSX

**Locais:** [montagem dos fragmentos](/C:/Faculdade/2026/PMI/workmy/backend-fastapi/src/infrastructure/documents/dashboard_excel.py:132) e [serialização de células](/C:/Faculdade/2026/PMI/workmy/backend-fastapi/src/infrastructure/documents/excel_rows.py:24).

O código aproveita um template do XlsxWriter e substitui o XML das linhas. Isso torna a tarefa divisível, mas cria responsabilidade própria sobre o formato da planilha. Há dependência da estrutura do XML do template, incluindo a linha técnica usada para descobrir os estilos. Datas e números também têm conversão própria.

**Proposta:** separar preparação, execução e montagem em métodos menores; representar os jobs com um tipo nomeado em vez da tupla de oito posições; verificar explicitamente a existência da linha técnica e dos estilos. Acrescentar casos de descrição formatada, texto no limite, caracteres incomuns e abertura dos arquivos no aplicativo de destino. As comparações com openpyxl são úteis, mas não equivalem a uma conferência visual no Excel.

### Baixa: corrigir documentação e reduzir duplicação

- [Docstring do worker](/C:/Faculdade/2026/PMI/workmy/backend-fastapi/src/infrastructure/documents/excel_rows.py:49) ainda menciona `ProcessPoolExecutor`, embora a implementação use `multiprocessing.Pool`. O relatório histórico reproduz esse trecho literalmente.
- [Índice dos documentos](/C:/Faculdade/2026/PMI/workmy/docs/README.md:12) ainda descreve um pipeline sequencial e comparação futura.
- `STAGES` aparece nos dois módulos do renderer; a cópia em `dashboard_excel.py` não é usada.
- `ExportarDashboardUseCase` depende diretamente de `starlette.concurrency`. Isso funciona, mas vincula a camada de aplicação ao framework web. Pode ser separado em uma evolução arquitetural, sem necessidade de reescrever o fluxo para a apresentação.
- Vários arquivos novos ainda estão fora do controle de versão. Os hashes preservam a evidência local, porém quem clonar apenas o commit-base não obterá essa implementação. Criar um commit revisado com código, testes e documentos relevantes e excluir temporários do pacote de entrega.

## 2. O que está bem resolvido

- Mesmo `render_rows` nos dois modos, sem trabalho descartável ou espera artificial.
- Divisão da planilha de pagamentos em blocos, reduzindo o desequilíbrio da estratégia anterior de um arquivo por processo.
- Workers sem sessão de banco nem workbook compartilhado. Temporários separados por exportação e por bloco.
- Consultas sequenciais no mesmo snapshot e montagem na ordem dos offsets.
- Textos serializados como texto, com testes de conteúdo que começa com `=`.
- ZIP externo sem nova compressão dos XLSX, que já são compactados.
- Verificação de integridade fora do intervalo cronometrado e preservação do resultado desfavorável ao paralelo.

## 3. Crítica da medição

Recalculei as estatísticas a partir das dez execuções de `comparacao-pool.json`. Os cinco arquivos-fonte registrados em `versao.json` mantêm os mesmos hashes. Não executei uma nova rodada de benchmark nesta revisão.

| Medida | Valor conferido |
| --- | ---: |
| Mediana sequencial | 15,5748 s |
| Mediana paralela | 12,7477 s |
| Diferença entre medianas | 2,8271 s |
| Redução do tempo | 18,1519% |
| Speedup | 1,2218× |
| Faixa sequencial | 11,1543 a 16,7675 s |
| Faixa paralela | 12,5353 a 14,5388 s |
| Pares em que o paralelo foi mais rápido | 4 de 5 |

**Pontos fortes:** cinco repetições, ordem alternada, conteúdo conferido e custo do pool incluído. A primeira execução favoreceu o sequencial e permanece visível.

**Limitações:** uma máquina, um volume principal, carga normal de outros processos, sem estudo de aquecimento, pico de recursos ou intervalo de confiança. Cinco pares oferecem evidência exploratória, não uma garantia de ganho universal. Alternar a ordem ajuda, mas não elimina variação de temperatura, cache e carga.

**Melhorias no benchmark:** registrar o commit/hash e limites de CPU/RAM em cada JSON; fazer aquecimento identificado e fora da amostra; registrar métricas de memória/disco; encerrar falhas com `status: failed` em vez de deixar apenas `running`; selecionar conta dedicada sem mudanças durante a série. Cada execução possui seu próprio snapshot: consistência interna não congela o banco entre execuções. A verificação de hashes detecta divergências posteriores.

O cronômetro `time.time()` começa antes do `print` de início, e `perf_counter()` começa depois desse `print`. É uma pequena diferença de escopo que pode aumentar se o terminal estiver lento. Para maior rigor, capturar os dois relógios juntos e imprimir fora do intervalo medido. Isso é uma melhoria metodológica; não demonstra que os 18,15% sejam inválidos.

**O que não dizer:** “o site ficou 18,2% mais rápido” ou “o paralelo sempre vence”. O ensaio mede consulta e geração dos arquivos, sem HTTP, download ou abertura no Excel. A afirmação correta é: “a mediana do tempo de geração caiu 18,2% neste ensaio”.

Os tempos de 32,21 s e 38,03 s pertencem ao algoritmo histórico por arquivo. Não devem ser combinados com 12,75 s para atribuir todo o ganho somente ao multiprocessing.

## 4. Atendimento aos requisitos do professor

### Atividade atual de paralelismo

Base da conferência: itens 1a–1d e 2a–2d registrados na seção 7 do relatório anterior. O material original do Classroom e o exemplo citado não estavam disponíveis para comparação independente nesta revisão. Assim, a avaliação é de aderência aos critérios registrados, não de aprovação acadêmica garantida.

| Critério registrado | Onde aparece | Avaliação |
| --- | --- | --- |
| Repositório clonado, se necessário | Slide 2 e relatório, seção 1 | Atendido pelo repositório existente; implementação ainda depende de alterações locais |
| Analisar oportunidade de desempenho | Slides 2 e 3 | Atendido: pagamentos concentram o trabalho |
| Registrar início, fim e duração | Slide 7, script e JSON | Atendido; horários completos dos dois modos no relatório |
| Implementar multiprocessing com pool | Slide 6 e código | Atendido literalmente com `get_context('spawn').Pool` |
| Relatar dificuldades | Slide 9 | Atendido, com problemas concretos |
| Comparar antes e depois | Slides 7 e 8 | Atendido com a mesma implementação; separar o histórico do slide 3 |
| Mostrar fonte sequencial e paralela | Slides 5 e 6 | Atendido; preparar os arquivos completos para perguntas |
| Discutir deadlocks, concorrência, escala e ganho | Slide 10 e relatório | Atendido como discussão; não foi feita prova de ausência de deadlocks ou teste de saturação |
| Exemplo do Classroom, caso obrigatório | Sem evidência de consulta | Não confirmado |

### Entrega anterior da N1: vídeo de até dez minutos

| Exigência informada pelo professor na conversa | Situação destes slides |
| --- | --- |
| Problema escolhido e solução do produto | Parcial: apresentam um problema técnico da exportação, sem desenvolver a necessidade do usuário do WorkMy |
| Organização da equipe | Nomes presentes; responsabilidades do desenvolvimento não documentadas nos slides |
| Processo de desenvolvimento | Presente apenas no recorte de otimização |
| Principais funcionalidades | Incompleto: foco na exportação, sem demonstração de clientes, serviços, projetos e financeiro |
| Testes e limitações | Presentes para a exportação |
| Próximos passos | Citados como limitações; falta uma sequência explícita de evolução do produto |
| Todos os integrantes participarem | Deve ser comprovado no vídeo; o roteiro distribui falas, mas não comprova gravação |
| Duração de até dez minutos | Depende do ensaio e da edição do vídeo |
| Link Drive/YouTube acessível | Não verificado nesta revisão |

Se o professor estiver avaliando a atividade de paralelismo, os slides atendem ao recorte. Se a entrega for o vídeo completo da N1, será necessário complementar o conteúdo do produto. A data da N1 informada anteriormente era 23/09/2026; o deck atual indica apresentação em 15/10/2026. Não tratar essas datas como uma única entrega.

## 5. Crítica da apresentação, slide a slide

Revisei visualmente as doze renderizações e extraí o texto do PPTX. Não observei texto cortado nas imagens. Não abri o arquivo no PowerPoint nativo nesta revisão.

| Slide | Avaliação e melhoria recomendada |
| --- | --- |
| 1 | Capa clara. Confirmar com o professor a identificação da atividade e a data antes da entrega |
| 2 | Explica a rotina e o volume. A fala deve dizer que os dados são fictícios e por que o usuário exporta |
| 3 | Boa exposição do experimento que piorou. Falta uma indicação mais visível de que os tempos são históricos e usam outro algoritmo |
| 4 | Fluxo correto. Há bastante espaço vazio acima das três etapas. Um diagrama de fluxo poderia facilitar a compreensão; é melhoria visual opcional |
| 5 | Código curto e legível. Fonte monoespaçada e recuo mais convencional facilitariam a leitura como Python |
| 6 | Mostra a biblioteca solicitada. Explicar `spawn`, `map` e worker, sem ler cada linha |
| 7 | Tabela honesta, inclusive no resultado negativo. Não ler todas as linhas. Início/fim do paralelo estão no relatório; poderiam aparecer também no slide |
| 8 | Valores e cálculo corretos. Padronizar vírgula decimal também nos rótulos do gráfico. Manter “mediana neste ensaio” na fala |
| 9 | Dificuldades específicas. Evitar gastar tempo demais com permissões do ambiente, que não são o ganho central do algoritmo |
| 10 | Aborda os desafios pedidos. Especificar oralmente que os quatro workers são por exportação e que não há limite global |
| 11 | Os 11 testes referem-se à evidência histórica da exportação e continuam válidos. A frase “falha de worker” é ampla: preferir “exceção tratada de worker”, pois morte abrupta/travamento não foram cobertos. “Limites verificados” seria mais preciso como “O que não foi medido” |
| 12 | Conclusão coerente. Acrescentar na fala a próxima etapa: controlar concorrência e medir memória antes de aumentar workers |

**Prioridade antes de apresentar:** dominar os slides 6–8, separar os dois experimentos e ensaiar a explicação dos limites. A fonte Helvetica Neue depende da instalação/substituição no computador de apresentação; conferir o deck nesse equipamento. A renderização validada não garante aparência idêntica em outro aplicativo.

## 6. Testes executados nesta revisão

| Verificação | Resultado | Evidência |
| --- | --- | --- |
| Suíte completa backend | 71 aprovados, 0 falhas/erros, 4 ignorados; 23,69 s | [JUnit backend](../../docs/evidencias/pmi-paralelismo-2026-10-13/revisao/testes-backend.xml) |
| Suíte completa frontend | 23 aprovados em 11 arquivos, 0 falhas; 17,12 s | [JUnit frontend](../../docs/evidencias/pmi-paralelismo-2026-10-13/revisao/testes-frontend.xml) |
| ESLint | Aprovado, saída 0 | Registro dos comandos abaixo |
| TypeScript e build Vite | Aprovados, saída 0 | Registro dos comandos abaixo |
| Arquivo da apresentação e fontes do benchmark | Hashes iguais aos da entrega analisada | [Auditoria](../../docs/evidencias/pmi-paralelismo-2026-10-13/revisao/auditoria.json) |
| Números e conteúdo do benchmark | Medianas recalculadas e hashes iguais nas dez execuções | Mesma auditoria e JSON original |

Total: **94 testes aprovados e 4 ignorados**, considerando backend e frontend. Os quatro ignorados são da carga histórica: carga completa, colisão de username, colisão de e-mail e rollback. Exigem PostgreSQL descartável, não configurado nesta execução. Não foram marcados como aprovados.

As primeiras tentativas no ambiente restrito falharam por restrições locais: event loop no backend e renomeação de temporários no Vitest. A repetição autorizada completou com os resultados acima. O [JUnit da tentativa restrita do frontend](../../docs/evidencias/pmi-paralelismo-2026-10-13/revisao/tentativa-frontend-sandbox.xml) foi preservado e não representa reprovação funcional dos casos.

Comandos finais, a partir das respectivas pastas:

```powershell
# backend-fastapi
.venv/Scripts/python.exe -m pytest -q --basetemp=../tmp/pytest-review-authorized-20261013 --junitxml=../docs/evidencias/pmi-paralelismo-2026-10-13/revisao/testes-backend.xml -o faulthandler_timeout=30

# frontend
npm run test -- --reporter=default --reporter=junit --outputFile=../docs/evidencias/pmi-paralelismo-2026-10-13/revisao/testes-frontend.xml
npm run lint
npm run build
```

Não foram executados nesta revisão: E2E no navegador, benchmark novo, abertura no Excel/PowerPoint nativo, saturação concorrente, morte abrupta de worker, medição de recursos e CI remoto. Os testes de API utilizam SQLite e os de componentes simulam a API. O benchmark histórico usa PostgreSQL real.

## 7. Entrega desta revisão

Esta revisão produziu a crítica, uma nova execução das verificações acima e o [roteiro dos slides](ROTEIRO_APRESENTACAO.md). A pedido do usuário, a identificação do terceiro participante foi atualizada para Leonardo no deck, no roteiro, neste relatório, no relatório técnico e no script de geração dos slides. Os tempos e as evidências do benchmark permanecem os mesmos, pois essa troca altera apenas a identificação dos apresentadores.

Referências locais: [relatório original](../../docs/evidencias/pmi-paralelismo-2026-10-13/RELATORIO_FINAL.md), [benchmark](../../docs/evidencias/pmi-paralelismo-2026-10-13/comparacao-pool.json) e [versão analisada](../../docs/evidencias/pmi-paralelismo-2026-10-13/versao.json).
