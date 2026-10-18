# Carga histórica sintética do WorkMy

O script `backend-fastapi/scripts/seed_historico.py` prepara uma conta exclusiva de testes. **Sem `--apply`, apenas gera e valida os dados em memória; não conecta ao banco.** Nenhuma conta foi criada no banco pessoal durante a implementação.

## Conteúdo

| Entidade | Quantidade |
| --- | ---: |
| Usuário | 1 |
| Clientes | 10.000 |
| Serviços | 53 |
| Projetos | 12.000 |
| Pagamentos mensais | 140.000 |
| Pagamentos avulsos | 60.000 |

São 222.054 registros ao todo, incluindo 200.000 pagamentos. Os dados são fictícios, sem imagens, comprovantes ou tags adicionais. A data de referência é fixa: **08/10/2026**. O gerador cobre todos os anos desde 2000 e usa a semente `200026`; `--seed` permite variar os valores, mantendo quantidades e regras.

Os 23 primeiros clientes são cadastrados em janeiro de 2026 e têm um contrato mensal ativo cada. Os valores são de R$ 750 a R$ 1.800, em incrementos de R$ 50, mais um contrato de R$ 1.950: **R$ 30.000/mês**. Os projetos atuais ficam distribuídos entre Planejamento, Andamento e Revisão. Os demais clientes/projetos são históricos, com projetos finalizados ou arquivados e recorrência desativada. Cada cliente tem pelo menos um projeto e as combinações cliente/serviço são únicas.

As mensalidades atuais de janeiro a agosto estão pagas; setembro e outubro ficam pendentes (46 cobranças, total R$ 60.000), permitindo exercitar filtros e atrasos. Os avulsos históricos variam de R$ 15 a R$ 250. O teto de R$ 30.230 aplica-se somente à soma dos contratos mensais ativos, não ao total histórico recebido nem ao saldo acumulado de pendências.

Distribuição padrão: 181.017 pagos, 46 pendentes, 6.990 cancelados e 11.947 estornados. Mensalidades têm referência única por projeto, valores constantes no respectivo contrato e sequência mensal sem lacunas. Todos os ajustes têm motivo. A data de entrega dos projetos históricos representa o encerramento sintético usado pelo gerador; não é adicionada uma coluna de encerramento. Pagamentos e ajustes históricos não ultrapassam essa data.

## Simulação local

Na raiz do repositório, com as dependências do backend instaladas:

```powershell
backend-fastapi/.venv/Scripts/python.exe backend-fastapi/scripts/seed_historico.py
```

Não precisa de `DATABASE_URL` ou senha para simular. O JSON final contém contagens, distribuição anual por vencimento, estados e soma dos contratos ativos. Execute sem `python -O`: o script rejeita otimizações que desabilitariam as verificações.

## Simulação pelo Docker

Na raiz do repositório, usando a imagem já construída do backend:

```powershell
$seedScript = Join-Path (Get-Location).Path 'backend-fastapi/scripts/seed_historico.py'
docker compose run --rm --no-deps --volume "${seedScript}:/app/seed_historico.py:ro" fastapi python /app/seed_historico.py
```

O script é montado somente para leitura: não é necessário alterar o Dockerfile ou reconstruir a imagem para incluí-lo. O comando substitui a inicialização normal da API e não executa migrations automaticamente.

## Aplicar quando desejar

O PostgreSQL do Compose deve estar disponível e com as migrations normais do projeto aplicadas. A conta `workmy_carga` e o e-mail `workmy.carga@example.com` não podem existir. Se houver colisão, o script encerra sem substituir dados ou senha.

No PowerShell 7, leia a senha sem deixá-la escrita no histórico:

```powershell
$seedScript = Join-Path (Get-Location).Path 'backend-fastapi/scripts/seed_historico.py'
$env:WORKMY_SEED_PASSWORD = Read-Host 'Defina a senha da conta workmy_carga' -MaskInput
try {
    docker compose run --rm --no-deps --env WORKMY_SEED_PASSWORD --volume "${seedScript}:/app/seed_historico.py:ro" fastapi python /app/seed_historico.py --apply
    if ($LASTEXITCODE -ne 0) { throw 'Carga não concluída; confira os pré-requisitos.' }
} finally {
    Remove-Item Env:WORKMY_SEED_PASSWORD -ErrorAction SilentlyContinue
}
```

O Compose fornece explicitamente a `DATABASE_URL` PostgreSQL. Para rodar fora do Docker, defina `DATABASE_URL` com a conexão PostgreSQL desejada e `WORKMY_SEED_PASSWORD`, e execute o mesmo script local com `--apply`. URLs SQLite são rejeitadas. Senha: mínimo de 6 caracteres, máximo de 72 bytes UTF-8, conforme bcrypt. A senha não aparece no relatório e não é persistida em texto puro.

Após uma execução com sucesso, entre no WorkMy usando **workmy_carga** ou **workmy.carga@example.com** e a senha definida por você. Essa conta só existe depois do commit da carga. A geração normal de recorrências no sistema, quando acionada depois da data de referência, pode acrescentar novas mensalidades; as contagens exatas descrevem o estado imediatamente após o seed.

## Transação e erros

- Inserções em lotes de 2.000, dentro de uma transação única. O JSON de sucesso é emitido depois do commit.
- IDs são gerados pelo banco, sem IDs fixos ou redefinição de sequências.
- Falha durante a carga desfaz usuário, cadastros e pagamentos inseridos. Sequências PostgreSQL podem apresentar lacunas mesmo após rollback; isso é normal.
- Não há opção de apagar ou recriar uma conta existente. Rodar novamente não duplica a carga.
- Os registros de outros usuários não são modificados. O novo usuário tem dados próprios; pagamentos pertencem a ele através dos projetos.
- Erros de drivers não são impressos integralmente para evitar exposição de parâmetros ou credenciais. O tipo da falha é mostrado; confira conexão, migrations, colisão da conta e variáveis de ambiente.
- Esta carga não é um benchmark nem uma garantia de desempenho da interface. Clientes e projetos têm listagens volumosas; o tempo de navegação depende das consultas e da paginação disponíveis no produto.

## Conferência SQL

Execute `docs/sql/conferir_carga_historica.sql` em uma conexão de leitura com o banco que recebeu a carga. As consultas filtram a conta de testes, mostram contagens, soma mensal, distribuição anual e inconsistências de vínculo ou de referência. O valor esperado para as consultas de inconsistência é zero.

## Testes automatizados

Sem PostgreSQL, execute na pasta `backend-fastapi`:

```powershell
.venv/Scripts/python.exe -m pytest tests/integration/test_seed_historico.py -q
```

Os testes de geração validam as 200.000 linhas, relações, datas, estados, referências e valores. Os testes de persistência são ignorados quando `WORKMY_SEED_TEST_DATABASE_URL` não está definida. Eles recusam qualquer banco cujo nome não seja `workmy_seed_test` e utilizam schemas temporários próprios.

Para um PostgreSQL descartável, sem volumes do WorkMy:

```powershell
docker run --detach --rm --name workmy-seed-test --publish 127.0.0.1:55439:5432 --env POSTGRES_DB=workmy_seed_test --env POSTGRES_USER=seed_test --env POSTGRES_PASSWORD=seed_test_local --tmpfs /var/lib/postgresql/data postgres:15-alpine
docker exec workmy-seed-test pg_isready -U seed_test -d workmy_seed_test
```

Espere `accepting connections`. Na pasta `backend-fastapi`:

```powershell
$env:WORKMY_SEED_TEST_DATABASE_URL = 'postgresql+asyncpg://seed_test:seed_test_local@127.0.0.1:55439/workmy_seed_test'
try {
    .venv/Scripts/python.exe -m pytest tests/integration/test_seed_historico.py -q
} finally {
    Remove-Item Env:WORKMY_SEED_TEST_DATABASE_URL -ErrorAction SilentlyContinue
    docker stop workmy-seed-test
}
```

Os testes criam tabelas dos modelos SQLAlchemy no schema descartável, carregam o volume completo, verificam bcrypt, colisões por usuário/e-mail e rollback após um lote de pagamentos. Não substituem a validação de migrations nem uma jornada autenticada no navegador.
