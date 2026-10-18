import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {FileBlob, PresentationFile} from '@oai/artifact-tool';

const root='C:/Faculdade/2026/PMI/workmy';
const build=path.join(root,'tmp/pmi-paralelismo-build');
const skill='C:/Users/rafae_9y1k772/.codex/plugins/cache/openai-primary-runtime/presentations/26.1013.11914/skills/presentations';
const template='C:/Users/rafae_9y1k772/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-simple-light-mode/assets/reference.pptx';
const benchmark=JSON.parse(await fs.readFile(path.join(root,'docs/evidencias/pmi-paralelismo-2026-10-13/comparacao-pool.json'),'utf8'));
const result=benchmark.results.total;
const seq=result.sequential.median_wall_time_seconds, par=result.parallel.median_wall_time_seconds;
const reduction=100*(1-par/seq);
const fmt=(v,n=2)=>v.toFixed(n).replace('.',',');
const deck=await PresentationFile.importPptx(await FileBlob.load(template));
const refs=[1,5,11,6,4,10,14,22,13,12,15,26];
const original=deck.slides.items;
const slides=refs.map(i=>original[i-1]);
deck.slides.keep(slides.map(s=>'sl/'+s.id));
deck.slides.reorder(slides.map(s=>'sl/'+s.id));
const font='Helvetica Neue';
const {applyPresentationChartFont}=await import('file:///'+skill+'/container_tools/artifact_tool_utils.mjs');
function put(slide,index,text,size=25,bold=false){
 const shape=slide.shapes.items[index];
 shape.text=text;
 shape.text.style={typeface:font,fontSize:size,bold,color:'#000000',alignment:'left',verticalAlignment:'top',autoFit:'none',wrap:'square',insets:0};
 return shape;
}
function title(s,i,t){put(s,i,t,38);}
function page(s,n){
 const num=s.shapes.items.find(sh=>/^\d+$/.test(String(sh.text).trim())&&sh.position.left>1000);
 if(num){num.text=String(n);num.text.style={typeface:font,fontSize:14,color:'#777777',alignment:'right'};}
}
function group(s,i,heading,body,size=25){
 const sh=put(s,i,'',size);
 sh.text=[{runs:[{run:heading,style:{bold:true,fontSize:(size+2)+'px',typeface:font}}],spaceAfter:12},
 {runs:[{run:body,style:{fontSize:size+'px',typeface:font}}]}];
 return sh;
}
function notes(s,text){s.speakerNotes.text=text;s.speakerNotes.setVisible(false);}

// Capa: clone da primeira página do modelo, com a tipografia e geometria originais.
put(slides[0],0,'WorkMy\nExportação com\nmultiprocessing',64);
put(slides[0],1,'PMI · Análise e Desenvolvimento de Sistemas\nRafael, Gabriel e Leonardo\nApresentação em 15/10/2026',25);
put(slides[0],2,'PROCESSAMENTO PARALELO',20);
notes(slides[0],'Fontes: enunciado fornecido pelo usuário e docs/evidencias/pmi-paralelismo-2026-10-13/RELATORIO_FINAL.md. A data de apresentação é 15/10/2026.');

// Rotina e identificação do repositório.
title(slides[1],2,'A rotina escolhida é a exportação Excel');
group(slides[1],3,'O que a função entrega',
 'O dashboard solicita um ZIP com quatro arquivos: Pagamentos, Clientes, Serviços e Projetos.\n\nO teste usa 200.000 pagamentos, 12.000 projetos, 10.000 clientes e 53 serviços.',26);
group(slides[1],4,'Onde fica no projeto',
 'Repositório já clonado: rafael-lass/workmy.\n\nExportarDashboardUseCase.run() coordena a leitura e chama o gerador.\n\nDashboardExcelRenderer.render() organiza os blocos e monta os arquivos.',26);
notes(slides[1],'Fontes: git remote -v conferido; backend-fastapi/src/application/usecases/exportar_dashboard.py; backend-fastapi/src/infrastructure/documents/dashboard_excel.py; comparacao-pool.json, campo counts. Base Git 6a97132 com alterações locais.');

// Oportunidade e experiência anterior que falhou.
title(slides[2],2,'A divisão por arquivo concentrou o trabalho');
group(slides[2],9,'Oportunidade encontrada',
 'Pagamentos tinha quase todo o custo. Um arquivo por processo deixava os outros workers ociosos. A melhoria divide também o conjunto grande em blocos de 25.000 linhas.',26);
put(slides[2],4,'Experimento inicial\nSequencial: 32,21 s\nParalelo: 38,03 s',27);
put(slides[2],7,'Nova distribuição\n8 blocos de pagamentos\n11 tarefas para 4 workers',27);
put(slides[2],5,'Abertura de processos e transporte das listas acrescentavam custo.',25);
put(slides[2],8,'Cada job referencia um bloco privado em disco. O worker processa linhas.',25);
notes(slides[2],'Fonte histórica: docs/evidencias/exportacao-excel-paralelo-2026-10-08/comparacao-apenas-renderizacao.json. Fonte atual: dashboard_excel.py, batch_size=25000 e workers=4. O experimento inicial usa algoritmo diferente e não integra as medianas atuais.');

// Diagrama funcional com as três colunas originais.
title(slides[3],2,'O pool executa blocos independentes');
group(slides[3],3,'1. Leitura e preparação',
 'Quatro consultas no mesmo snapshot do banco.\n\nA função divide as linhas e cria entradas privadas para cada bloco.',26);
group(slides[3],5,'2. Multiprocessing',
 'Pool com até quatro processos.\n\nCada worker calcula atraso, converte células e grava um fragmento próprio.',26);
group(slides[3],4,'3. Montagem e entrega',
 'O processo principal reúne os fragmentos na ordem original.\n\nMonta os quatro XLSX e entrega o ZIP.',26);
notes(slides[3],'Fontes: exportar_dashboard.py; dashboard_excel.py; excel_rows.py. Só o processamento dos blocos executa em multiprocessing. Banco e montagem final seguem sequenciais. Não há workbook nem sessão SQLAlchemy compartilhada.');

// Código-fonte sequencial real.
title(slides[4],3,'O sequencial processa um bloco por vez');
put(slides[4],0,'def run_sequential(jobs):\n    return [\n        render_rows(job)\n        for job in jobs\n    ]',28);
group(slides[4],4,'A mesma função nos dois modos',
 'render_rows(job) calcula campos e serializa as linhas.\n\nO sequencial executa todas as tarefas no processo principal.\n\nMesmos blocos, formatos, cálculos e dados usados na versão paralela.',26);
notes(slides[4],'Fonte real: dashboard_excel.py, função run_sequential. A quebra de linha foi expandida para legibilidade; o comportamento é idêntico ao source. O worker compartilhado está em excel_rows.py, render_rows.');

// Pool direto da biblioteca exigida.
title(slides[5],2,'O paralelo usa multiprocessing.Pool');
put(slides[5],3,'Quatro workers em uma máquina\ncom quatro CPUs visíveis',29);
const code=put(slides[5],6,
 'from multiprocessing import get_context\ndef run_parallel(jobs, workers):\n    if not jobs:\n        return []\n    with get_context("spawn").Pool(\n        processes=min(workers, len(jobs))\n    ) as pool:\n        return pool.map(render_rows, jobs)',23);
code.position={...code.position,top:294,height:350,width:680};
for (const [idx,t] of [[4,'Contexto spawn'],[7,'Pool de processos reais'],[9,'map distribui as tarefas'],[11,'Fragmentos exclusivos'],[13,'with encerra o pool']]) put(slides[5],idx,t,25);
notes(slides[5],'Fonte real: dashboard_excel.py, função run_parallel. As linhas da chamada Pool foram quebradas para exibição. benchmark_excel.py usa if __name__ == __main__, necessário ao spawn. A máquina da medição informa cpu_count=4.');

// Medição: preserva a tabela do modelo, adaptando linhas e largura de colunas.
title(slides[6],2,'Início, fim e duração ficam registrados');
const first=benchmark.runs[0];
put(slides[6],3,
 `Exemplo sequencial de 13/10: início ${first.started_at.slice(11,23)}, fim ${first.finished_at.slice(11,23)} (São Paulo).\nTempo = time.time() no fim − time.time() no início. Cinco repetições por modo.`,24);
const table=slides[6].tables.items[0];
table.deleteRows({index:7,count:2});
const values=[['Repetição','Sequencial (s)','Paralelo (s)','Economia (s)','Mais rápido']];
for(let rep=1;rep<=5;rep++){
 const a=benchmark.runs.filter(r=>r.repetition===rep);
 const s=a.find(r=>r.mode==='sequential').wall_time_seconds;
 const p=a.find(r=>r.mode==='parallel').wall_time_seconds;
 values.push([String(rep),fmt(s,3),fmt(p,3),fmt(s-p,3),s>p?'Paralelo':'Sequencial']);
}
values.push(['Medianas',fmt(seq,3),fmt(par,3),'—','Paralelo']);
for(let r=0;r<values.length;r++)for(let c=0;c<5;c++){
 const cell=table.getCell(r,c);cell.value=values[r][c];
 cell.text.style={typeface:font,fontSize:23,bold:r===0||r===6,color:'#000000'};
 cell.fill=r===0?'#EDEDED':'#FFFFFF';
}
notes(slides[6],'Fonte: docs/evidencias/pmi-paralelismo-2026-10-13/comparacao-pool.json. Horários started_at/finished_at são reais com offset -03:00. Repetições alternam ordem. Tempos incluem todo run(), abertura/encerramento de processos e ZIP. Hashes são conferidos fora do cronômetro. Tempos de uma repetição podem favorecer o sequencial.');

// Gráfico editável no lugar do gráfico de amostra do modelo.
title(slides[7],2,`A mediana paralela reduz o tempo em ${fmt(reduction,1)}%`);
const existing=slides[7].charts.items[0];
const chartInspection=await deck.inspect({kind:'chart',maxChars:10000});
const chartAnchor=chartInspection.ndjson.split('\n').filter(Boolean).map(line=>JSON.parse(line)).find(item=>item.kind==='chart');
deck.delete(chartAnchor.id);
const chart=slides[7].charts.add('bar',{
 position:{left:66.61,top:158.84,width:528.06,height:470.32},
 title:'Duração total (segundos)',titleTextStyle:{fontSize:24},
 categories:['Sequencial','Pool, 4 workers'],
 series:[{name:'Tempo mediano',values:[Number(seq.toFixed(2)),Number(par.toFixed(2))],fill:'#3D8DFF'}],
 hasLegend:false,barOptions:{direction:'column',gapWidth:90},
 yAxis:{min:0,max:20,majorUnit:5,numberFormatCode:'0',textStyle:{fontSize:20}},
 xAxis:{textStyle:{fontSize:20}},
 dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.00',textStyle:{fontSize:23}},
 chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF'
});
applyPresentationChartFont(chart,{fontFamily:font});
put(slides[7],3,`${fmt(seq)} s`,56);
put(slides[7],4,'Mediana sequencial',25);
put(slides[7],5,`${fmt(par)} s`,56);
put(slides[7],6,'Mediana com Pool',25);
group(slides[7],8,'Comparação da mesma implementação',
 `Economia: ${fmt(seq-par)} segundos.\nSpeedup: ${fmt(seq/par)}×.\nCinco execuções em cada modo.`,27);
notes(slides[7],'Fonte: comparacao-pool.json, results.total. Python 3.12.15, PostgreSQL 15, Docker Linux/WSL2, 4 CPUs. Redução = 100*(1-par/seq); speedup=seq/par. O gráfico começa em zero. Essa comparação não usa resultados do algoritmo anterior. A medição inclui carga normal e variação de execução no computador.');

// Dificuldades concretas.
title(slides[8],2,'Dificuldades encontradas na implementação');
group(slides[8],3,'Distribuição desigual',
 'Um processo concentrava Pagamentos. Blocos de 25.000 linhas distribuíram o maior conjunto.',25);
group(slides[8],4,'Custo de iniciar processos',
 'O pool tem custo de abertura. Os jobs carregam caminhos de arquivos privados e metadados pequenos.',25);
group(slides[8],5,'Preservação dos arquivos',
 'A montagem precisa manter ordem, moeda, datas e texto. Testes e hashes conferem a equivalência.',25);
group(slides[8],6,'Ambiente e cronometragem',
 'Permissões de temporários e suspensão do sistema afetaram ensaios. Docker e dois relógios ajudam a validar os tempos.',25);
notes(slides[8],'Fontes: RELATORIO_FINAL.md, seção dificuldades; históricos preservados em docs/evidencias/exportacao-excel-paralelo-2026-10-08. Não afirmar deadlock onde houve problema de permissão ou relógio.');

// Desafios pedidos no enunciado.
title(slides[9],2,'Deadlocks, concorrência e escalabilidade');
put(slides[9],11,'Os testes mostram o comportamento deste ambiente. O ganho depende do volume e dos recursos disponíveis.',26);
group(slides[9],6,'Deadlocks',
 'Nenhum observado. Workers usam arquivos distintos e não compartilham banco ou workbook. Falhas e I/O ainda exigem atenção.',23);
group(slides[9],4,'Concorrência',
 'Um diretório por exportação e um fragmento por bloco. Só o processo principal monta XLSX e ZIP.',23);
group(slides[9],10,'Escalabilidade',
 'Até quatro workers. Memória, disco e exportações simultâneas limitam a expansão. Mais workers não garantem ganho linear.',23);
group(slides[9],8,'Ganho limitado',
 'Leitura, preparação e montagem seguem seriais. Volumes pequenos podem perder tempo ao iniciar processos.',23);
notes(slides[9],'Fontes: dashboard_excel.py, excel_rows.py e RELATORIO_FINAL.md, seção desafios. Nenhum deadlock observado não prova ausência de risco. Não foram medidos pico de memória/disco nem múltiplas exportações simultâneas. A API usa tempo limite HTTP, que não cancela automaticamente um worker preso.');

// Evidência e limites.
title(slides[10],2,'A comparação preservou o conteúdo');
group(slides[10],11,'Validação da exportação',
 '11 testes aprovados.\n\nMesmo conteúdo dos quatro workbooks nas dez execuções da medição.\n\nBanco PostgreSQL real no benchmark e SQLite isolado nos testes de API.',27);
put(slides[10],4,'Integridade',24,true);put(slides[10],3,'SHA-256 do XML das células, estilos e estrutura em todos os arquivos.',24);
put(slides[10],6,'Ordenação',24,true);put(slides[10],5,'Blocos se reúnem pelos offsets, preservando a ordem das consultas.',24);
put(slides[10],8,'Tratamento de falhas',24,true);put(slides[10],7,'Falha de worker impede a entrega parcial e limpa os temporários.',24);
put(slides[10],10,'Limites verificados',24,true);put(slides[10],9,'Sem estudo de pico de recursos ou concorrência de várias exportações.',24);
notes(slides[10],'Fontes: testes.xml (11 testes, zero falhas), comparacao-pool.json content_equal=true e content_sha256 de cada run. Tests: test_excel_blocks.py e test_dashboard_excel.py. Hashes ignoram timestamps ZIP. Evidências não constituem ensaio concorrente de vários usuários.');

// Conclusão, no layout de encerramento do template.
put(slides[11],0,'O pool distribui o\ntrabalho dos pagamentos',62);
put(slides[11],1,`${fmt(seq)} s sequencial\n${fmt(par)} s com multiprocessing\n${fmt(reduction,1)}% menos tempo nesta medição`,27);
slides[11].shapes.items[1].position={...slides[11].shapes.items[1].position,width:820};
put(slides[11],2,'WORKMY',20);
notes(slides[11],'Fontes: comparacao-pool.json e RELATORIO_FINAL.md. A melhoria é demonstrada para este volume/ambiente. Instruções de apresentação e comandos da demo ficam no chat conforme solicitado, fora dos slides.');

for(let i=0;i<slides.length;i++)page(slides[i],i+1);
await fs.mkdir(path.join(build,'draft'),{recursive:true});
const candidate=path.join(build,'draft/workmy-paralelismo.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidate);
for(let i=0;i<slides.length;i++){
 const png=await deck.export({slide:slides[i],format:'png',scale:1});
 await fs.writeFile(path.join(build,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
const {finalizePresentation}=await import('file:///'+skill+'/container_tools/artifact_tool_utils.mjs');
const finalPath=path.join(root,'output/pmi-paralelismo/WorkMy_Paralelismo_PMI_15-10-2026_Leonardo.pptx');
const referenceHash=crypto.createHash('sha256').update(await fs.readFile(template)).digest('hex');
const validated=await finalizePresentation({
 workspaceDir:root,candidatePath:candidate,finalPath,
 explicitTotalSlideCount:12,
 pythonExecutable:'C:/Users/rafae_9y1k772/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','7'],
 requiredNativeTableOwnerSlides:[7],requiredNativeChartOwnerSlides:[8],
 materializeLiteralChartWorkbooks:true,
 fontPolicy:{basis:'reference',families:[font],referencePath:template,referenceSha256:referenceHash},
 verifyArtifactToolImport:true,
 receiptPath:path.join(build,'validation-leonardo.json')
});
console.log(JSON.stringify({finalPath,validated}));
