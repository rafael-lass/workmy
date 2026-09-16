# Requisitos funcionais

## Produto e público

O WorkMy atende profissionais autônomos e pequenos prestadores que precisam controlar a entrega e o recebimento dos seus serviços. As áreas públicas do produto são Dashboard, Projetos, Clientes, Serviços e Financeiro.

## Autenticação

- Login aceita usuário ou e-mail.
- O BFF mantém access e refresh tokens apenas em cookies HTTP-only.
- O frontend valida a sessão por `GET /auth/me`; dados privados não são persistidos em `localStorage`.
- Cadastro valida e mascara telefone brasileiro; telefone é opcional.

## Clientes e serviços

- Cliente exige nome; empresa, e-mail e telefone são opcionais.
- Serviço exige nome único por usuário. Imagem aceita PNG, JPEG ou WebP de até 5 MiB.
- Descrição visual (Tiptap): títulos, negrito, itálico, listas, citações e links HTTP(S)/mailto. Documento JSON versionado, validado no backend, com até 20 mil caracteres. Sem HTML arbitrário ou imagens embutidas.
- Até 10 tags por serviço, com até 40 caracteres por nome, selecionáveis de um catálogo privado e reutilizável. Espaços e caixa são normalizados para evitar duplicatas. Remover uma seleção não exclui a tag.
- Visualização completa e apresentação comercial em PDF A4. O profissional revisa nome, e-mail e telefone antes de baixar; estes ajustes não alteram sua conta. O PDF usa somente dados do serviço salvo, capa e contatos informados, sem dados financeiros ou de clientes.
- Repositório e ferramentas não são expostos; colunas legadas e dados existentes permanecem preservados na migração.
- Clientes e serviços vinculados a projetos não podem ser excluídos.
- Total recebido considera somente lançamentos `PAGO`.

## Projetos

- Um projeto vincula um cliente a um serviço e nasce em Descoberta, com progresso 0%.
- Etapas: `DISCOVERY`, `IN_PROGRESS`, `REVIEW`, `COMPLETED`, `ARCHIVED`.
- Transições válidas: Descoberta → Em andamento/Arquivado; Em andamento → Revisão/Arquivado; Revisão → Em andamento/Concluído/Arquivado; Concluído → Arquivado.
- Concluir ou arquivar pausa a recorrência.
- Um projeto com qualquer histórico financeiro não pode ser excluído; deve ser arquivado.

## Modelo financeiro

Estados e transições:

```text
PENDENTE ── receber ──► PAGO ── estornar ──► ESTORNADO
    └──── cancelar ──► CANCELADO
```

- Cancelado e estornado são terminais.
- Atrasado é calculado: `PENDENTE` com `data_vencimento` anterior à data de negócio em São Paulo.
- Recebimento avulso manual nasce `PAGO`; mensalidade gerada nasce `PENDENTE`.
- Não há pagamento parcial. O valor de cada lançamento é integral e imutável.
- Somente observação e comprovante podem ser alterados depois da criação.
- Cancelamento e estorno exigem motivo.
- Comprovante aceita PDF, PNG, JPEG ou WebP de até 5 MB.
- Dashboard, cliente e projeto somam somente registros `PAGO`; estornos saem do realizado.

## Recorrência

- Alterar valor ou vencimento afeta somente cobranças futuras.
- Pausar não cancela pendências existentes.
- Retomar exige valor, vencimento e uma nova data inicial; meses pausados não são gerados.
- A ação manual de faturamento cria todas as referências vencidas ausentes desde o início/retomada até hoje.
- A geração é síncrona por HTTP, idempotente e protegida também por restrição única no banco.

## Interfaces financeiras

- `GET /pagamentos`: filtros por status, tipo, cliente, projeto, período e busca; resposta paginada.
- `POST /pagamentos`: recebimento avulso já pago.
- `PATCH /pagamentos/{id}/receber`: confirma pendência.
- `PATCH /pagamentos/{id}/cancelar` e `/estornar`: exigem motivo.
- `PATCH /pagamentos/{id}/detalhes`: altera observação/comprovante.
- `POST /faturamento/recorrencias`: retorna quantidade, valor total e referências criadas.
- `GET /dashboard/resumo`: indicadores, série de seis meses e cinco recebimentos recentes.

Não há `PUT` ou `DELETE` genérico de pagamentos.

## Fora de escopo

Pagamentos parciais, gateway, emissão fiscal, recuperação de senha, geração automática em segundo plano, RabbitMQ, CSV, vínculo em massa, indicadores de leads, propostas personalizadas, colaboração em tempo real e funcionalidades completas do Notion.
