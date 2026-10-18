# WorkMy - Roteiro N1 PMI IV

Duração planejada: 9min40s. Rafael, Gabriel e Tais participam. Uma pessoa pode controlar a tela durante todo o vídeo. A divisão das falas é sugerida; relatar a divisão real do trabalho. Abrir o PDF de apresentação, WorkMy em http://localhost:5173, Trello e relatório de testes antes de gravar. Ensaiar uma vez com cronômetro. A conta demo tem Studio Aurora, Gestão de redes sociais, projeto mensal de R$ 300 e mensalidade de setembro paga. Não registrar a mesma mensalidade novamente.

## 0:00-1:20 | Rafael | Abertura, problema e solução

**Onde mostrar:** PDF páginas 1 e 2; depois Dashboard.

### Fala sugerida

Olá, professor. Nós somos Rafael, Gabriel e Tais, do curso de Análise e Desenvolvimento de Sistemas. Vamos apresentar o MVP do WorkMy, uma aplicação para organizar clientes, serviços, projetos e recebimentos.

O problema escolhido é a dificuldade de centralizar a gestão de pequenos serviços. Quando os dados ficam distribuídos entre mensagens, anotações e planilhas, fica mais difícil identificar o que foi contratado, em qual etapa está o trabalho e quais valores ainda precisam ser recebidos. A proposta atende profissionais autônomos e pequenos prestadores de serviço.

O WorkMy reúne essas informações em um único sistema. O usuário cadastra clientes e serviços, relaciona esses registros em projetos e acompanha a execução e os recebimentos. Neste MVP priorizamos esse fluxo principal e um dashboard financeiro. A demonstração utiliza o ambiente local executado com Docker.

### Ações na tela

Mostrar os nomes na página 1. Avançar para problema e solução. Abrir o dashboard e apontar recebido no mês e previsão, ambos R$ 300. Não mostrar senha na gravação.

## 1:20-2:05 | Tais | Organização da equipe

**Onde mostrar:** PDF página 3; Trello real do WorkMy.

### Fala sugerida

O acompanhamento do projeto está organizado em um quadro técnico com as listas A fazer, Em desenvolvimento, Em teste, Concluído e Bloqueado. Os cartões descrevem funcionalidades e melhorias do produto, com objetivo, critérios de aceite, testes e evidências.

Neste cartão podemos consultar o comportamento esperado e como ele será verificado. Isso ajuda a identificar o que foi implementado e quais validações ainda estão pendentes. Uma implementação existente não significa que todos os cenários já foram validados em todos os ambientes.

### Ações na tela

Abrir um cartão real, preferencialmente WM-017. Mostrar critérios e evidências. Acrescentar uma frase curta sobre as atividades efetivamente realizadas por cada integrante. A divisão das falas não comprova autoria do código. Se o quadro real divergir do slide, descrever o quadro real.

## 2:05-2:55 | Gabriel | Clientes e serviços

**Onde mostrar:** WorkMy: Clientes; Serviços; editar Gestão de redes sociais. PDF página 4 como apoio.

### Fala sugerida

O fluxo começa pelo cliente. Aqui utilizamos o Studio Aurora, um cadastro fictício preparado para a apresentação. Esse registro será relacionado aos serviços contratados por meio dos projetos.

No catálogo de serviços temos Gestão de redes sociais. A descrição está dividida em objetivo, entregas e modo de execução. O editor permite títulos, negrito, listas, citações e links, deixando a proposta mais organizada. As tags ajudam a identificar os serviços. Também existe a geração de uma apresentação comercial em PDF.

### Ações na tela

Abrir o cliente existente. Abrir a edição do serviço, mostrar a descrição e aplicar uma formatação simples. Salvar apenas se necessário. Mostrar a opção de PDF; usar arquivo previamente gerado se a operação consumir tempo.

## 2:55-4:45 | Gabriel | Projetos e financeiro

**Onde mostrar:** WorkMy: Projetos → Financeiro → Dashboard.

### Fala sugerida

O projeto relaciona o Studio Aurora ao serviço de Gestão de redes sociais. Neste exemplo, o contrato é mensal, no valor de trezentos reais, e está em Planejamento. O fluxo usa Planejamento, Andamento, Revisão e Finalizado. O acompanhamento ocorre pelas etapas, sem percentual de progresso.

Podemos avançar o trabalho e utilizar os filtros para localizar os projetos. O arquivamento é separado das etapas de execução.

No financeiro, a mensalidade de setembro já está registrada como paga. Este recebimento é fictício e foi preparado para a demonstração. Também podemos abrir o formulário de registro de recebimento, selecionar o serviço e o cliente associado e informar os dados da operação.

Voltando ao dashboard, temos trezentos reais recebidos no mês e previsão de trezentos reais para o mês seguinte. As informações conectam o andamento dos serviços à situação financeira.

### Ações na tela

Avançar Planejamento para Andamento uma única vez. Mostrar títulos dos filtros e Todos. Abrir Financeiro e o lançamento PAGO de setembro. Abrir Registrar recebimento, demonstrar a seleção e cancelar, sem duplicar a mensalidade. Voltar ao dashboard. Não arquivar o único projeto antes de mostrar a previsão: isso altera sua elegibilidade. Não demonstrar CSV sem verificar sua existência na versão local.

## 4:45-5:45 | Rafael | Requisitos e regras

**Onde mostrar:** PDF página 5.

### Fala sugerida

Os requisitos funcionais descrevem o que o sistema oferece: autenticação, cadastro de clientes e serviços, gerenciamento de projetos, registro de recebimentos e consulta do dashboard.

Os requisitos não funcionais tratam de características como segurança de acesso, persistência, adaptação da interface e reprodução do ambiente com Docker. Esses requisitos devem estar ligados a verificações concretas.

As regras de negócio definem restrições. Os dados pertencem ao usuário autenticado. Cobranças mensais não devem se repetir para o mesmo projeto e referência. Cancelamentos e estornos exigem motivo. Projetos com histórico financeiro têm restrições de exclusão para preservar esse histórico.

### Ações na tela

Apontar RF, RNF e RN conforme explica. Não ler uma lista extensa de requisitos. Usar as regras como exemplos relacionados à demonstração anterior.

## 5:45-6:40 | Rafael | Arquitetura e banco

**Onde mostrar:** PDF páginas 6 e 7.

### Fala sugerida

A interface utiliza React e TypeScript e é servida pelo Nginx. As solicitações passam pelo BFF, desenvolvido com Node.js e Express, que intermedeia a comunicação e participa do gerenciamento da sessão com cookies HTTP-only. A API utiliza Python com FastAPI. O backend separa domínio, casos de uso e infraestrutura.

O banco é PostgreSQL, com acesso por SQLAlchemy e alterações de estrutura versionadas com Alembic. As principais entidades são usuários, clientes, serviços, projetos e pagamentos. Um projeto relaciona cliente e serviço, e os pagamentos ficam associados ao projeto. Serviços também possuem tags. O Docker Compose organiza os serviços do ambiente.

### Ações na tela

Seguir as setas da arquitetura. Explicar BFF como intermediário entre interface e API. Passar à página 7 ao falar das entidades. Não atribuir versões de bibliotecas que não foram verificadas.

## 6:40-8:15 | Tais | Testes, evidências e reteste

**Onde mostrar:** PDF página 8; docs/trello/evidencias/2026-09-21-reteste-WM017/RELATORIO.md e previsao.log.

### Fala sugerida

Utilizamos pytest no backend e Vitest com Testing Library no frontend. A execução documentada de vinte e um de setembro registrou cinquenta e cinco testes de backend e quinze de frontend aprovados, totalizando setenta testes sem falhas na rodada final. Essa evidência corresponde à versão identificada no relatório e não representa um reteste de todas as alterações posteriores.

Um defeito encontrado envolvia a previsão financeira. Com setembro como referência, um contrato vigente de trezentos reais e outro de novecentos reais iniciado somente em novembro, a previsão de outubro deveria ser trezentos reais. Antes, o resultado era mil e duzentos reais.

A correção passou a compartilhar a regra de primeiro vencimento entre faturamento e dashboard. O reteste comprovou trezentos reais, conforme esperado. Quatro cenários falharam antes da correção; a execução final ficou aprovada. Os logs e relatórios JUnit preservam as evidências.

Os testes de API e persistência dessa execução usam SQLite, e os componentes usam chamadas simuladas. Isso não comprova a jornada completa no navegador com PostgreSQL nem o comportamento concorrente nesse banco.

### Ações na tela

Mostrar resumo do relatório e data. Abrir previsao.log e apontar Esperado 300.00, Obtido 300.00, APROVADO. Não somar o diagnóstico adicional aos 70. O cenário com contrato futuro é um teste automatizado; a conta demo possui apenas o contrato de R$ 300. Revisão funcional de Tais consta pendente na evidência histórica.

## 8:15-9:10 | Gabriel | Dificuldades e próximos passos

**Onde mostrar:** PDF página 9; backlog técnico, se disponível.

### Fala sugerida

As dificuldades técnicas incluem manter as regras financeiras consistentes, tratar datas de recorrência, preservar o histórico e manter a interface alinhada à API.

Como evolução, planejamos ampliar os testes de navegador com Playwright contra o ambiente Docker, validar migrations e concorrência com PostgreSQL e aumentar a cobertura do BFF na renovação de sessão e no envio de arquivos.

Também pretendemos continuar melhorando a experiência de uso e manter a documentação ligada aos requisitos, às implementações e às evidências. O backlog técnico permite acompanhar essas atividades e suas dependências.

### Ações na tela

Mostrar WM-018, WM-019, WM-020 e WM-021 caso ainda estejam pendentes no quadro. Não apresentar tarefas já concluídas como futuras. Distinguir validação automatizada de revisão funcional humana.

## 9:10-9:40 | Rafael | Encerramento

**Onde mostrar:** PDF página 10; todos podem aparecer na câmera.

### Fala sugerida

O WorkMy entrega um fluxo que conecta o cadastro de clientes e serviços ao acompanhamento de projetos e recebimentos. A proposta do MVP é centralizar essas informações e facilitar a organização do prestador de serviços.

Mostramos as funcionalidades disponíveis, a arquitetura, as regras principais e as evidências de teste, além dos limites e das melhorias planejadas. Obrigado pela atenção.

### Ações na tela

Manter a página final visível e encerrar até 9 minutos e 40 segundos. Não incluir a senha da conta no vídeo. Compartilhar o vídeo com acesso liberado para avaliação.
