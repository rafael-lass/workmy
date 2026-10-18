# Validação do script de carga histórica

Data: 08/10/2026. Escopo: novo gerador, sem carga no banco pessoal do WorkMy.

## Resultados

- Simulação padrão: 10.000 clientes, 53 serviços, 12.000 projetos e 200.000 pagamentos validados.
- 140.000 mensalidades e 60.000 avulsos; todos os anos de 2000 a 2026 representados.
- 23 clientes com contratos mensais ativos; soma R$ 30.000.
- Suite dedicada: **10 testes aprovados**, sem falhas ou ignorados, em 41,99 segundos.
- Evidência automatizada: [JUnit](pytest.xml).

Comando executado na pasta `backend-fastapi`, com `WORKMY_SEED_TEST_DATABASE_URL` apontando exclusivamente ao banco descartável `workmy_seed_test`:

```powershell
.venv/Scripts/python.exe -m pytest tests/integration/test_seed_historico.py -q -p no:cacheprovider --junitxml=../tmp/seed-historico-postgres.xml
```

## Cobertura

1. Volume completo em memória e invariantes de datas, estados, referências, vínculos e teto mensal.
2. Reprodutibilidade e variação por semente.
3. Rejeição de conexão ausente, vazia ou SQLite (três cenários).
4. Simulação padrão sem criação de conexão pelo script.
5. Carga integral com commit no PostgreSQL e verificação de contagens, relacionamentos e senha bcrypt.
6. Colisão por username e por e-mail, mantendo a conta existente intacta (dois cenários).
7. Falha após o primeiro lote de pagamentos: rollback deixa todas as tabelas da carga vazias.

## Ambiente e limites

PostgreSQL 15 Alpine em container próprio, porta local 55439, armazenamento em tmpfs, sem volumes do WorkMy. Cada teste de persistência utiliza um schema temporário independente, removido ao terminar. Os testes criaram as tabelas pelos modelos SQLAlchemy; não afirmam validação das migrations. O tempo informado é da suite, não é benchmark da aplicação.

A primeira tentativa sob execução restrita não conectou ao container e foi interrompida. A execução com permissão de acesso ao PostgreSQL descartável completou e gerou o JUnit vinculado acima.

Não foram executados testes de navegador, carga HTTP, frontend, login pelo BFF ou benchmark. Nenhum usuário ou pagamento desta carga foi inserido no banco pessoal. Aplicação real e conferência pós-carga permanecem a cargo da futura execução com `--apply`.
