# Requisitos não funcionais — WorkMy

[Índice](README.md) · [Funcionais](REQUISITOS_FUNCIONAIS.md) · [Não funcionais](REQUISITOS_NAO_FUNCIONAIS.md) · [Regras de negócio](REGRAS_DE_NEGOCIO.md)

**Atualização:** 21/09/2026 · **Base:** `21274ca` + correção local WM-017, ainda sem commit/push.

## Finalidade

Os requisitos não funcionais descrevem **qualidade, segurança e condições de operação**. A tabela distingue mecanismos existentes de validações ainda pendentes.

## Catálogo e situação de validação

| ID | Requisito não funcional | Implementação e evidência disponível |
| --- | --- | --- |
| RNF-01 | Proteger credenciais e sessão. | Senhas com bcrypt, autenticação JWT e cookies HTTP-only no BFF. Testes de autenticação aprovados; cobertura completa da renovação no BFF está pendente. |
| RNF-02 | Isolar dados entre usuários. | Validações de propriedade implementadas e cenários de acesso cobertos por testes de API. |
| RNF-03 | Preservar integridade e histórico financeiro. | Regras de domínio, exclusão lógica e restrições únicas implementadas. Testes aprovados; concorrência real em PostgreSQL ainda pendente. |
| RNF-04 | Persistir dados entre reinicializações. | PostgreSQL com volume Docker configurado. Reinicialização e recuperação não foram demonstradas nesta execução. |
| RNF-05 | Permitir instalação reproduzível. | Docker Compose e migrations Alembic disponíveis. Execução integrada do ambiente ainda precisa ser registrada. |
| RNF-06 | Tratar falhas sem perder dados já preenchidos nos formulários. | Testes de componentes confirmam preservação de formulários após falha e bloqueio de envio duplicado em fluxos específicos. |
| RNF-07 | Oferecer interface utilizável por teclado e em diferentes tamanhos de tela. | Diálogo possui testes de título acessível, Escape e retorno de foco. Validação completa de responsividade e acessibilidade permanece pendente. |
| RNF-08 | Facilitar manutenção e verificação de alterações. | Backend separado em camadas, testes automatizados e workflow de CI configurado. Não foi verificada execução remota do pipeline nesta etapa. |

## Critérios de verificação

| ID | Como verificar | Pendência ou limite |
| --- | --- | --- |
| RNF-01 | Rejeitar credenciais inválidas; guardar senhas como hash e tokens em cookies HTTP-only; validar renovação e encerramento da sessão. | Cobertura completa do BFF pendente (WM-020). Revogação do access token em memória do processo. |
| RNF-02 | Tentar consultar ou alterar recursos do usuário B autenticado como A e confirmar a rejeição. | Cenários de API cobertos; jornada integrada ainda pendente. |
| RNF-03 | Rejeitar duplicidades, transições inválidas e exclusão de projeto com histórico; confirmar que estornos saem do realizado. | Testes aprovados em SQLite; concorrência no PostgreSQL pendente (WM-019). |
| RNF-04 | Gravar dados, reiniciar os serviços mantendo o volume e confirmar a persistência; testar restauração de backup. | Configuração existente; execução desse roteiro não registrada. |
| RNF-05 | Subir ambiente isolado com Docker Compose, aplicar migrations e percorrer uma jornada autenticada. | Execução E2E do conjunto pendente (WM-018). |
| RNF-06 | Simular falha da API e verificar formulário preservado, erro visível e nova tentativa; impedir envios duplicados. | Aprovado nos componentes cobertos; não equivale a testar todas as telas. |
| RNF-07 | Usar teclado para abrir/fechar diálogos e recuperar foco; verificar telas em larguras de 390 e 1440 pixels. | Testes de diálogo aprovados; revisão responsiva e auditoria ampla de acessibilidade pendentes. |
| RNF-08 | Executar suítes, localizar regras nas camadas e conferir relatórios; verificar execução do workflow remoto. | Suítes locais aprovadas; pipeline remoto não verificado nesta rodada. |

## Evidências atuais

- **55 testes de backend e 15 de frontend aprovados**, totalizando 70 na rodada após a correção WM-017.
- API e persistência: SQLite em memória/temporário; casos de uso também utilizam repositórios de teste.
- Interface: Vitest, jsdom e chamadas de API simuladas.
- Não há comprovação nesta rodada de E2E com PostgreSQL, teste de carga, revisão funcional de Tais ou validação com usuários externos.

[Relatório do reteste WM-017](trello/evidencias/2026-09-21-reteste-WM017/RELATORIO.md) · [Inventário dos 70 testes](trello/evidencias/2026-09-21-reteste-WM017/INVENTARIO.md)

## Metas ainda não medidas

Não foram definidos ou comprovados limites de tempo de resposta, quantidade de usuários simultâneos ou disponibilidade percentual. Esses números precisam de metas acordadas e testes específicos antes de serem apresentados como resultados do produto.

## Referências

[Arquitetura](ARQUITETURA.md) · [Guia do desenvolvedor](DEVELOPER_GUIDE.md) · [Backlog técnico](trello/README.md)
