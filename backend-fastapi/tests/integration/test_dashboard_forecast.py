from datetime import date, datetime
from decimal import Decimal

from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.infrastructure.persistence.session import Base
from src.infrastructure.persistence.models import UsuarioModel, ClienteModel, ServicoModel, ProjetoModel
from src.infrastructure.persistence.repositories.postgres_dashboard_query import PostgresDashboardQuery


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        for user_id in (1, 2):
            session.add(UsuarioModel(id=user_id, username=f'user{user_id}', email=f'{user_id}@example.com', password_hash='test'))
            session.add(ClienteModel(id=user_id, usuario_id=user_id, nome=f'Cliente {user_id}'))
        await session.flush()
        yield session
    await engine.dispose()


async def add_project(session, **overrides):
    user = overrides.get('usuario_id', 1)
    service = ServicoModel(usuario_id=user, nome=f'Serviço {uuid4()}')
    session.add(service)
    await session.flush()
    values = dict(usuario_id=user, cliente_id=user, servico_id=service.id,
                  tipo_recorrencia='MENSAL', recorrencia_ativa=True,
                  valor_mensal=Decimal('900.00'), dia_vencimento=5,
                  recorrencia_inicio=date(2026, 9, 1), criado_em=datetime(2026, 9, 1))
    values.update(overrides)
    session.add(ProjetoModel(**values))
    await session.flush()


@pytest.mark.parametrize('start,expected', [
    (date(2026, 11, 1), '300.00'),
    (date(2026, 10, 1), '1200.00'),
    (date(2026, 10, 5), '1200.00'),
    (date(2026, 10, 6), '300.00'),
], ids=['future-start', 'before-due', 'on-due', 'after-due'])
async def test_forecast_first_eligible_due_date(session, start, expected):
    await add_project(session, valor_mensal=Decimal('300.00'))
    await add_project(session, recorrencia_inicio=start)
    result = await PostgresDashboardQuery(session).get_resumo(1, date(2026, 9, 21))
    assert isinstance(result['previsto_proximo_mes'], str)
    assert Decimal(result['previsto_proximo_mes']) == Decimal(expected)


@pytest.mark.parametrize('overrides', [
    {'recorrencia_ativa': False}, {'status': 'COMPLETED'}, {'status': 'ARCHIVED'},
    {'deletado_em': datetime(2026, 9, 20)}, {'usuario_id': 2},
    {'tipo_recorrencia': 'AVULSO', 'recorrencia_ativa': False},
], ids=['paused', 'completed', 'archived', 'deleted', 'other-user', 'one-off'])
async def test_forecast_excludes_ineligible_contracts(session, overrides):
    await add_project(session, valor_mensal=Decimal('300.00'))
    await add_project(session, **overrides)
    result = await PostgresDashboardQuery(session).get_resumo(1, date(2026, 9, 21))
    assert Decimal(result['previsto_proximo_mes']) == Decimal('300.00')


@pytest.mark.parametrize('created,expected', [
    (datetime(2026, 10, 5), '900.00'), (datetime(2026, 10, 6), '0.00'),
], ids=['creation-on-due', 'creation-after-due'])
async def test_forecast_falls_back_to_creation(session, created, expected):
    await add_project(session, recorrencia_inicio=None, criado_em=created)
    result = await PostgresDashboardQuery(session).get_resumo(1, date(2026, 9, 21))
    assert Decimal(result['previsto_proximo_mes']) == Decimal(expected)


async def test_forecast_year_boundary(session):
    await add_project(session, recorrencia_inicio=date(2027, 1, 5))
    await add_project(session, recorrencia_inicio=date(2027, 1, 6))
    result = await PostgresDashboardQuery(session).get_resumo(1, date(2026, 12, 21))
    assert Decimal(result['previsto_proximo_mes']) == Decimal('900.00')


async def test_forecast_empty(session):
    result = await PostgresDashboardQuery(session).get_resumo(1, date(2026, 9, 21))
    assert Decimal(result['previsto_proximo_mes']) == Decimal('0.00')
