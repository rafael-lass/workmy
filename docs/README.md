# Documentação do WorkMy

A documentação mantida junto ao código foi reduzida às referências que refletem a aplicação atual:

- [Requisitos funcionais](REQUISITOS_FUNCIONAIS.md): funcionalidades implementadas, fluxos e evoluções planejadas.
- [Requisitos não funcionais](REQUISITOS_NAO_FUNCIONAIS.md): segurança, qualidade, operação e situação das validações.
- [Regras de negócio](REGRAS_DE_NEGOCIO.md): restrições, estados, recorrência e condições financeiras.
- [Arquitetura](ARQUITETURA.md): responsabilidades de Front, BFF, API e banco.
- [Guia do desenvolvedor](DEVELOPER_GUIDE.md): execução, testes e entrega com Docker e `uv`.
- [CI/CD e hospedagem gratuita](DEPLOY_CLOUD.md): Vercel, Render e Supabase, configuração dos painéis, HTTPS, sessão e recuperação.
- [Serviços](SERVICOS.md): editor visual, catálogo de tags, migração e PDF comercial.
- [Carga histórica sintética](CARGA_HISTORICA.md): script de simulação e carga opcional de 200 mil pagamentos em uma conta exclusiva.
- [Exportação Excel](EXPORTACAO_EXCEL.md): abas, períodos, pipeline sequencial e benchmark para futura comparação com multiprocessing.
- [Backlog técnico e cartões do Trello](trello/README.md): entregas identificadas no código, próximas melhorias, casos de teste e evidências; separado dos materiais acadêmicos.

Documentos de planejamento da arquitetura antiga foram removidos porque descreviam RabbitMQ, SSE e componentes que não fazem parte do produto.
