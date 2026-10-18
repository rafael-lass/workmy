# Exportação Excel: evidências da versão de arquivo único

> **Atenção:** esta evidência registra a versão anterior, que produzia um único XLSX com várias abas e dashboard. Ela não representa a versão atual, que produz um ZIP com quatro arquivos XLSX separados e sem dashboard. Não compare diretamente estes tempos com medições do novo formato.

Data: 08/10/2026. Base Git: `6a97132e56da6fdc48e0e76894661251fa779639`, mais alterações locais; não representa um commit publicado. Ambiente de medição: Python 3.12 no container FastAPI, PostgreSQL 15 do Compose, mesma conta sintética `workmy_carga` e referência fixa 08/10/2026. Detalhes de plataforma e CPUs estão no JSON.

## Tempos medidos

Foram realizadas três execuções de cada período pelo mesmo `ExportarDashboardUseCase.run()` usado na API. Valores abaixo são medianas do pipeline, incluindo consultas, resumo e escrita/compactação. Não incluem transferência HTTP nem abertura no Excel.

| Período | Pagamentos | Clientes | Serviços | Projetos | Tempo mediano |
| --- | ---: | ---: | ---: | ---: | ---: |
| 3 meses | 69 | 23 | 23 | 23 | 0,063 s |
| 6 meses | 138 | 23 | 23 | 23 | 0,066 s |
| 12 meses | 230 | 23 | 23 | 23 | 0,218 s |
| Total | 200.000 | 10.000 | 53 | 12.000 | 39,034 s |

A execução Total gerou aproximadamente 17,9 MB decimais (17,1 MiB). Tempos totais individuais: 34,949 s; 39,034 s; 40,157 s. A mediana da etapa de escrita XLSX foi 34,825 s; consulta de pagamentos, 3,389 s; resumo, 0,670 s. Medianas calculadas por etapa não precisam somar a mediana do total.

Evidência completa: [sequencial.json](sequencial.json). Os arquivos são apagados após cada repetição. A primeira execução é mantida, sem descarte de aquecimento. Os resultados dependem do hardware, caches e carga do ambiente.

**Paralelo: não implementado e não medido**, conforme escolha do usuário. Não há speedup calculado. A predominância da escrita indica que paralelizar apenas o resumo não elimina a maior parte do tempo; essa hipótese deve ser testada na evolução futura.

## Validação do download real da versão anterior

Foi realizada autenticação no BFF e download Total pela rota antiga `http://localhost:5173/api/dashboard/exportar.xlsx?periodo=total`, passando por Nginx, BFF e API.

- HTTP 200, MIME XLSX e nome `workmy-relatorio-total-2026-10-08.xlsx`.
- 17.915.017 bytes recebidos; observação de tempo HTTP: 43,735 s. Essa chamada ocorreu durante outras verificações, não compõe a baseline.
- A checagem do diretório temporário da API após o download encontrou zero arquivos `workmy-export-*.xlsx`.
- Evidência HTTP: [http.json](http.json).
- Conferência do conteúdo: [download-validado.json](download-validado.json), com contagens e reconciliação dos valores da aba Pagamentos com o Dashboard.

## Testes e verificações

- Backend completo: **68 aprovados, 4 ignorados**, zero falhas. [JUnit backend](backend.xml).
- Os quatro ignorados são testes opcionais da carga histórica em PostgreSQL isolado, cuja variável de conexão não foi definida nesta execução. Não são testes de exportação reprovados.
- Frontend completo: **23 aprovados**, zero falhas. [JUnit frontend](frontend.xml).
- Build TypeScript/Vite, lint ESLint e verificação sintática do BFF aprovados.
- Docker reconstruído para API, BFF e frontend. Download real confirmado no ambiente atualizado.

Os testes de exportação da versão anterior usaram SQLite isolado para cenários controlados e Openpyxl para inspecionar o arquivo. A validação da versão atual é registrada separadamente: testes específicos confirmam as quatro planilhas individuais dentro do ZIP, ausência de dashboard, filtragem, autenticação e limpeza dos temporários.

Não foi feita validação em Microsoft Excel instalado, teste de múltiplos downloads concorrentes ou medição de memória máxima. A escrita é incremental, mas o conjunto consultado permanece em memória. O teste HTTP e benchmark com PostgreSQL complementam, sem substituir, uma jornada de navegador automatizada.

## Reprodução e próxima comparação

Consulte [EXPORTACAO_EXCEL.md](../../EXPORTACAO_EXCEL.md). Preserve este diretório ao medir outras versões. Para comparar multiprocessing no futuro, mantenha dados, critérios, ambiente e volume; conte o custo dos processos e confira a equivalência das células e dos totais antes de comparar tempos.
