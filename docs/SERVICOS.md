# Serviços: descrição visual e apresentação comercial

O formulário canônico contém nome, capa, descrição e tags. O editor Tiptap é carregado apenas na área de Serviços. A visualização usa o mesmo esquema do editor, sem inserir HTML arbitrário.

## API autenticada

- `GET /api/servicos/tags`: catálogo do profissional.
- `POST /api/servicos/tags`, `{nome}`: cria ou retorna a tag normalizada existente. Unicidade no banco por usuário e nome normalizado, com tratamento de concorrência.
- `POST /api/servicos/` e `PUT /api/servicos/{id}`: `{nome, imagem_base64, descricao_documento, tag_ids}`. Respostas incluem `tags: [{id, nome}]` e `descricao_resumo` de até 240 caracteres.
- `POST /api/servicos/{id}/pdf`: `{nome_profissional, email, telefone?}`. Retorna `application/pdf`, attachment com filename seguro e `Cache-Control: no-store`. Ausência de sessão retorna 401; serviço alheio retorna 404.

`descricao_documento` aceita null ou `{version: 1, doc: {type: "doc", content: [...]}}`. Elementos: paragraph, heading (nível 1–3), text, hardBreak, bulletList, orderedList, listItem e blockquote. Marcas: bold, italic, link. Links permitem HTTP, HTTPS e mailto. Limites: 20.000 caracteres de texto, 5.000 nós e 12 níveis. Capa separada de até 5 MiB.

## Persistência e migração

`20260916_0002` adiciona descrição JSON, catálogo de tags e associação serviço/tag. Converte descrições antigas em parágrafos e deduplica tags por profissional. IDs, imagens, projetos e colunas legadas não são apagados. Nomes legados acima de 40 caracteres são truncados somente no novo catálogo; o texto original continua preservado. Serviços legados com mais de 10 tags mantêm os vínculos; na próxima edição será necessário selecionar até 10.

Atualização normal: `docker compose up -d --build`. O startup executa `uv run --frozen --no-sync alembic upgrade head`. **Não execute `down -v` para atualizar**. Faça backup antes de migrações em produção. Downgrade remove o novo documento e catálogo; colunas legadas não são sincronizadas com novas edições.

## PDF e limites de escopo

O caso de uso carrega e autoriza o serviço. O renderizador ReportLab recebe uma entidade e contatos, sem acesso à rede. A rota executa a renderização síncrona via thread pool; não há fila, worker ou RabbitMQ. Fontes Bitstream Vera e licença vêm empacotadas na dependência ReportLab congelada pelo uv. Imagens locais são decodificadas, redimensionadas proporcionalmente e reencodadas. Capas legadas inválidas são omitidas.

O cliente HTTP lê blobs somente em respostas bem-sucedidas, preserva erros JSON e usa o tratamento central de sessão expirada. O BFF encaminha bytes e Content-Disposition sem serialização JSON.

Não é uma proposta personalizada: não inclui preço, cliente, pagamento ou informação interna de projeto. Não há colaboração em tempo real nem funções completas do Notion.
