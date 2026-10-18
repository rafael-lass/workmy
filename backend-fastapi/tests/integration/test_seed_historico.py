"""PostgreSQL opcional: exclusivamente DATABASE workmy_seed_test."""
from itertools import islice
import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import func, insert, select, text
from sqlalchemy.ext.asyncio import create_async_engine

from scripts import seed_historico as seed
from src.infrastructure.persistence.session import Base
from src.infrastructure.security.jwt_service import hash_password, verify_password


@pytest.fixture(scope='module')
def data():
    return seed.generate()


def test_complete_generation_and_business_invariants(data):
    report = seed.validate_and_report(data)
    assert report['contagens']['pagamentos'] == 200000
    assert report['estados']['PENDENTE'] == 46
    assert report['mensalidades_ativas'] == '30000'
    assert len([c for c in data[0] if c['criado_em'].year == 2026]) == 23
    assert all(p['data_entrega'].year <= 2025 for p in data[2] if not p['recorrencia_ativa'])


def test_reproducibility(data):
    assert seed.generate() == data
    assert list(islice(seed.payments(data[2]), 500)) == list(islice(seed.payments(data[2]), 500))
    assert seed.generate(42)[2] != data[2]


@pytest.mark.parametrize('url', [None, '', 'sqlite+aiosqlite:///test.db'])
def test_explicit_postgres_required(url):
    with pytest.raises(ValueError):
        seed.postgres_url(url)


def test_default_cli_does_not_connect(monkeypatch, capsys):
    monkeypatch.setattr(seed.sys, 'argv', ['seed_historico.py'])
    def forbidden(*args, **kwargs):
        pytest.fail('Simulação não pode criar conexão de banco.')
    monkeypatch.setattr(seed, 'create_async_engine', forbidden)
    assert seed.main() == 0
    assert 'simulação sem conexão' in capsys.readouterr().out


@pytest_asyncio.fixture
async def pg():
    value = os.getenv('WORKMY_SEED_TEST_DATABASE_URL')
    if not value:
        pytest.skip('PostgreSQL descartável não configurado')
    url = seed.postgres_url(value)
    if url.database != 'workmy_seed_test':
        pytest.fail('Teste permitido somente no banco workmy_seed_test.')
    schema = 'seed_test_' + uuid.uuid4().hex
    admin = create_async_engine(url, connect_args={'timeout': 5})
    async with admin.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA {schema}'))
    engine = create_async_engine(url, connect_args={'timeout': 5, 'server_settings': {'search_path': schema}})
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield engine
    finally:
        await engine.dispose()
        async with admin.begin() as conn:
            await conn.execute(text(f'DROP SCHEMA {schema} CASCADE'))
        await admin.dispose()


async def test_postgres_full_load_and_account(pg, data):
    password = 'Only-for-isolated-test-2026'
    async with pg.begin() as conn:
        uid = await seed.load(conn, data, hash_password(password))
    async with pg.connect() as conn:
        user = (await conn.execute(select(seed.UsuarioModel.__table__).where(seed.UsuarioModel.id == uid))).mappings().one()
        assert verify_password(password, user['password_hash'])
        assert user['username'] == seed.USERNAME
        assert await conn.scalar(text('SELECT COUNT(*) FROM pagamentos')) == 200000
        assert await conn.scalar(text('SELECT COUNT(DISTINCT cliente_id) FROM projetos WHERE recorrencia_ativa')) == 23
        assert await conn.scalar(text('SELECT SUM(valor_mensal) FROM projetos WHERE recorrencia_ativa')) == 30000
        assert await conn.scalar(text('SELECT COUNT(*) FROM projetos p JOIN clientes c ON c.id=p.cliente_id JOIN servicos s ON s.id=p.servico_id WHERE p.usuario_id <> c.usuario_id OR p.usuario_id <> s.usuario_id')) == 0
        assert await conn.scalar(text('SELECT COUNT(*) FROM pagamentos pg JOIN projetos p ON p.id=pg.projeto_id WHERE pg.data_vencimento < p.criado_em::date OR pg.data_pagamento > DATE \'2026-10-08\'')) == 0


@pytest.mark.parametrize('collision', ['username', 'email'])
async def test_postgres_collision_preserves_existing_account(pg, data, collision):
    u = seed.UsuarioModel.__table__
    async with pg.begin() as conn:
        await conn.execute(insert(u).values(username=seed.USERNAME if collision == 'username' else 'existing',
            email=seed.EMAIL if collision == 'email' else 'existing@example.com', password_hash='unchanged'))
    with pytest.raises(ValueError, match='já existe'):
        async with pg.begin() as conn:
            await seed.load(conn, data, 'new-hash')
    async with pg.connect() as conn:
        assert await conn.scalar(select(func.count()).select_from(u)) == 1
        assert await conn.scalar(select(u.c.password_hash)) == 'unchanged'
        assert await conn.scalar(select(func.count()).select_from(seed.ClienteModel)) == 0


async def test_postgres_failure_after_payment_batch_rolls_back(pg, data, monkeypatch):
    original = seed.payments
    def interrupted(*args, **kwargs):
        yield from islice(original(*args, **kwargs), 2001)
        raise RuntimeError('Falha simulada após lote gravado')
    monkeypatch.setattr(seed, 'payments', interrupted)
    with pytest.raises(RuntimeError, match='Falha simulada'):
        async with pg.begin() as conn:
            await seed.load(conn, data, 'test-hash')
    async with pg.connect() as conn:
        for model in (seed.UsuarioModel, seed.ClienteModel, seed.ServicoModel, seed.ProjetoModel, seed.PagamentoModel):
            assert await conn.scalar(select(func.count()).select_from(model)) == 0
