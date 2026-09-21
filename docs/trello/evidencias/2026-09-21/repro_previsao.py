"""Reproduce WM-017 against an isolated in-memory database; no application data.

From the repository root:
backend-fastapi/.venv/Scripts/python.exe docs/trello/evidencias/2026-09-21/repro_previsao.py
This is a diagnostic, not a passing regression test or an implementation fix.
"""
import asyncio
from datetime import date
from decimal import Decimal
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'backend-fastapi'))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.infrastructure.persistence.session import Base
from src.infrastructure.persistence.models import UsuarioModel, ClienteModel, ServicoModel, ProjetoModel
from src.infrastructure.persistence.repositories.postgres_dashboard_query import PostgresDashboardQuery


async def main():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            session.add(UsuarioModel(id=1, username='teste', email='teste@example.com', password_hash='not-a-login'))
            session.add(ClienteModel(id=1, usuario_id=1, nome='Cliente Teste'))
            session.add_all([
                ServicoModel(id=1, usuario_id=1, nome='Contrato vigente'),
                ServicoModel(id=2, usuario_id=1, nome='Contrato futuro'),
            ])
            await session.flush()
            for service_id, amount, start in [
                (1, '300.00', date(2026, 9, 1)),
                (2, '900.00', date(2026, 11, 1)),
            ]:
                session.add(ProjetoModel(
                    usuario_id=1, cliente_id=1, servico_id=service_id,
                    tipo_recorrencia='MENSAL', recorrencia_ativa=True,
                    valor_mensal=Decimal(amount), recorrencia_inicio=start,
                    dia_vencimento=5,
                ))
            await session.flush()
            result = await PostgresDashboardQuery(session).get_resumo(1, date(2026, 9, 21))
            expected = Decimal('300.00')
            actual = Decimal(result['previsto_proximo_mes'])
            print('CT-WM017 - Previsao do proximo mes')
            print('Ambiente: SQLite em memoria; dados descartados ao encerrar.')
            print('Data de referencia: 2026-09-21; mes previsto: 2026-10')
            print('Contrato vigente: 300.00 desde 2026-09-01; vencimento dia 5')
            print('Contrato futuro: 900.00 desde 2026-11-01; vencimento dia 5')
            print(f'Esperado: {expected:.2f}')
            print(f'Obtido: {actual:.2f}')
            print('Status:', 'APROVADO' if actual == expected else 'REPROVADO - defeito reproduzido')
            print('Diagnostico concluido; nenhuma correcao aplicada.')
    finally:
        await engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
