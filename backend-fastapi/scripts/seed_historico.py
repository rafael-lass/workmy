"""Carga sintética isolada por usuário. Sem --apply, não conecta ao banco."""
import argparse
import asyncio
from collections import Counter
from datetime import date, datetime, timedelta
from decimal import Decimal
import json
import os
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import insert, select, or_, func
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from src.domain.entities.pagamento import PagamentoEntity
from src.domain.entities.projeto import ProjetoEntity
from src.domain.service_document import validate_document
from src.domain.time import business_today
from src.infrastructure.persistence.models import (
    UsuarioModel, ClienteModel, ServicoModel, ProjetoModel, PagamentoModel,
)

REFERENCE = date(2026, 10, 8)
USERNAME = 'workmy_carga'
EMAIL = 'workmy.carga@example.com'
BATCH = 2000


def stamp(day):
    return datetime.combine(day, datetime.min.time())


def month(offset):
    return date(2000 + offset // 12, offset % 12 + 1, 5)


def generate(seed=200026):
    """Índices locais são convertidos em IDs reais apenas durante a inserção."""
    rng = random.Random(seed)
    services = []
    kinds = ['Design', 'Consultoria', 'Manutenção', 'Desenvolvimento', 'Marketing', 'Suporte', 'Fotografia']
    areas = ['digital', 'comercial', 'editorial', 'institucional', 'web', 'criativo', 'operacional', 'estratégico']
    for i in range(53):
        services.append(dict(nome=f'{kinds[i % 7]} {areas[i // 7]} {i + 1:02}',
            descricao_documento={'version': 1, 'doc': {'type': 'doc', 'content': [
                {'type': 'heading', 'attrs': {'level': 2}, 'content': [{'type': 'text', 'text': 'Escopo do serviço'}]},
                {'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Serviço fictício: planejamento, execução, revisão e entrega. Carga histórica para testes.'}]},
            ]}}, criado_em=stamp(date(2000, 1, 1))))
    projects = []
    historical_monthlies = 6990
    remaining_monthlies = 140000 - 230
    avulsos = 12000 - 23 - historical_monthlies
    for i in range(12000):
        client = i if i < 10000 else 23 + (i - 10000)
        service = 0 if i < 10000 else 1
        # Ciclo de serviços sem repetir a combinação do primeiro projeto do cliente.
        service = (client % 53 + service) % 53
        current = i < 23
        monthly = current or i < 23 + historical_monthlies
        if current:
            start, end, count = date(2026, 1, 1), REFERENCE, 10
            value = Decimal(750 + 50 * i) if i < 22 else Decimal(1950)
        elif monthly:
            j = i - 23
            count = remaining_monthlies // historical_monthlies + (j < remaining_monthlies % historical_monthlies)
            offset = (j * 37) % 288
            start = month(offset).replace(day=1)
            end = month(offset + count - 1) + timedelta(days=20)
            value = Decimal(rng.randrange(15000, 250001)) / 100
        else:
            j = i - 23 - historical_monthlies
            count = 60000 // avulsos + (j < 60000 % avulsos)
            start = date(2000, 1, 1) + timedelta(days=(j * 71) % 8800)
            end = start + timedelta(days=count * 7 + 20)
            value = None
        projects.append(dict(cliente_id=client, servico_id=service,
            status=['DISCOVERY', 'IN_PROGRESS', 'REVIEW'][i % 3] if current else ('COMPLETED' if i % 2 else 'ARCHIVED'),
            progresso=0, tipo_recorrencia='MENSAL' if monthly else 'AVULSO',
            recorrencia_ativa=current, valor_mensal=value, valor=None,
            dia_vencimento=5, recorrencia_inicio=start if monthly else None,
            criado_em=stamp(start), data_entrega=None if current else end,
            _count=count, _end=end))
    first_dates = {i: REFERENCE for i in range(10000)}
    for p in projects:
        first_dates[p['cliente_id']] = min(first_dates[p['cliente_id']], p['criado_em'].date())
    clients = []
    names = ['Aurora', 'Horizonte', 'Ipê', 'Maré', 'Serra', 'Jardim', 'Luar', 'Ponte']
    sectors = ['Studio', 'Oficina', 'Ateliê', 'Loja', 'Escritório']
    for i in range(10000):
        name = f'{sectors[i % 5]} {names[i % 8]} {i + 1:05}'
        clients.append(dict(nome=name, empresa=name, email=f'cliente{i+1:05}@example.com', criado_em=stamp(first_dates[i])))
    return clients, services, projects


def payments(projects, seed=200026):
    rng = random.Random(seed + 1)
    for i, p in enumerate(projects):
        monthly = p['tipo_recorrencia'] == 'MENSAL'
        start = p['criado_em'].date()
        for n in range(p['_count']):
            due = month((start.year - 2000) * 12 + start.month - 1 + n) if monthly else start + timedelta(days=n * 7 + 1)
            state = 'PAGO'
            if p['recorrencia_ativa'] and n >= 8:
                state = 'PENDENTE'
            elif monthly and n % 20 == 18:
                state = 'CANCELADO'
            elif n % 20 == 19 or (not monthly and n == 3):
                state = 'ESTORNADO'
            paid = due + timedelta(days=2) if state in ('PAGO', 'ESTORNADO') else None
            changed = (paid + timedelta(days=1)) if state == 'ESTORNADO' else (paid or due)
            yield dict(projeto_id=i, valor=p['valor_mensal'] if monthly else Decimal(rng.randrange(1500, 25001)) / 100,
                tipo_pagamento='MENSAL' if monthly else 'AVULSO', status=state,
                data_vencimento=due, data_pagamento=paid,
                referencia_mes=due.strftime('%Y-%m') if monthly else None,
                gerado_automaticamente=monthly,
                observacao='Dado sintético para teste de volume; não corresponde a uma transação real.',
                motivo_ajuste='Ajuste fictício de teste.' if state in ('ESTORNADO', 'CANCELADO') else None,
                criado_em=stamp(due), atualizado_em=stamp(changed), status_alterado_em=stamp(changed))


def validate_and_report(data, seed=200026):
    clients, services, projects = data
    assert (len(clients), len(services), len(projects)) == (10000, 53, 12000)
    for s in services:
        validate_document(s['descricao_documento'])
    pairs, active, used = set(), [], set()
    for p in projects:
        fields = {k: v for k, v in p.items() if not k.startswith('_') and k not in ('progresso', 'data_entrega')}
        ProjetoEntity(usuario_id=1, **fields).validate()
        pair = (p['cliente_id'], p['servico_id'])
        assert pair not in pairs
        pairs.add(pair); used.add(p['cliente_id'])
        assert clients[p['cliente_id']]['criado_em'] <= p['criado_em']
        assert services[p['servico_id']]['criado_em'] <= p['criado_em']
        if p['recorrencia_ativa']:
            active.append(p)
    assert len(used) == 10000
    assert len(active) == len({p['cliente_id'] for p in active}) == 23
    total_active = sum(p['valor_mensal'] for p in active)
    assert total_active == Decimal('30000')
    years, states, types, references = Counter(), Counter(), Counter(), set()
    for row in payments(projects, seed):
        PagamentoEntity(**row).validate()
        p = projects[row['projeto_id']]
        assert p['criado_em'].date() <= row['data_vencimento'] <= p['_end'] <= REFERENCE
        assert row['criado_em'] <= row['status_alterado_em'] == row['atualizado_em'] <= stamp(REFERENCE)
        if row['data_pagamento']:
            assert row['data_vencimento'] <= row['data_pagamento'] <= p['_end']
        if row['referencia_mes']:
            key = row['projeto_id'], row['referencia_mes']
            assert key not in references
            references.add(key)
            assert row['referencia_mes'] == row['data_vencimento'].strftime('%Y-%m')
        else:
            assert Decimal('15') <= row['valor'] <= Decimal('250')
        if row['status'] == 'PENDENTE':
            assert p['recorrencia_ativa']
        years[row['data_vencimento'].year] += 1
        states[row['status']] += 1
        types[row['tipo_pagamento']] += 1
    assert sum(years.values()) == 200000
    assert set(years) == set(range(2000, 2027))
    assert types == {'MENSAL': 140000, 'AVULSO': 60000}
    return dict(reference=str(REFERENCE), seed=seed, usuario=USERNAME,
        contagens=dict(usuarios=1, clientes=len(clients), servicos=len(services), projetos=len(projects), pagamentos=sum(years.values())),
        clientes_mensais_ativos=len(active), mensalidades_ativas=str(total_active),
        pagamentos_por_ano=dict(sorted(years.items())), estados=dict(states), tipos=dict(types))


async def insert_batches(conn, table, rows, return_ids=False):
    batch, ids = [], []
    async def flush():
        query = insert(table)
        if return_ids:
            query = query.returning(table.c.id, sort_by_parameter_order=True)
        result = await conn.execute(query, batch)
        if return_ids:
            ids.extend(result.scalars().all())
    for row in rows:
        batch.append(row)
        if len(batch) == BATCH:
            await flush(); batch.clear()
    if batch:
        await flush()
    return ids


async def load(conn, data, password_hash, seed=200026):
    """Chamador deve abrir uma transação; não faz commit parcial."""
    u, c, s, p, pay = [m.__table__ for m in (UsuarioModel, ClienteModel, ServicoModel, ProjetoModel, PagamentoModel)]
    existing = await conn.scalar(select(u.c.id).where(or_(u.c.username == USERNAME, u.c.email == EMAIL)))
    if existing is not None:
        raise ValueError('Usuário ou e-mail da carga já existe; nenhuma alteração realizada.')
    uid = await conn.scalar(insert(u).values(username=USERNAME, email=EMAIL, password_hash=password_hash).returning(u.c.id))
    clients, services, projects = data
    ci = await insert_batches(conn, c, (dict(row, usuario_id=uid) for row in clients), True)
    si = await insert_batches(conn, s, (dict(row, usuario_id=uid) for row in services), True)
    project_rows = (dict({k: v for k, v in row.items() if not k.startswith('_')}, usuario_id=uid,
        cliente_id=ci[row['cliente_id']], servico_id=si[row['servico_id']]) for row in projects)
    pi = await insert_batches(conn, p, project_rows, True)
    await insert_batches(conn, pay, (dict(row, projeto_id=pi[row['projeto_id']]) for row in payments(projects, seed)))
    for table, expected in ((c,10000),(s,53),(p,12000)):
        actual = await conn.scalar(select(func.count()).select_from(table).where(table.c.usuario_id == uid))
        if actual != expected:
            raise ValueError('Contagem persistida divergente; carga cancelada.')
    actual = await conn.scalar(select(func.count()).select_from(pay.join(p)).where(p.c.usuario_id == uid))
    if actual != 200000:
        raise ValueError('Contagem de pagamentos divergente; carga cancelada.')
    return uid


def postgres_url(value):
    if not value:
        raise ValueError('Informe DATABASE_URL explicitamente para --apply.')
    url = make_url(value)
    if url.get_backend_name() != 'postgresql':
        raise ValueError('A carga exige PostgreSQL; SQLite não é permitido.')
    return url.set(drivername='postgresql+asyncpg')


async def apply(data, seed):
    url = postgres_url(os.getenv('DATABASE_URL'))
    password = os.getenv('WORKMY_SEED_PASSWORD', '')
    if len(password) < 6 or len(password.encode('utf-8')) > 72:
        raise ValueError('WORKMY_SEED_PASSWORD deve ter ao menos 6 caracteres e até 72 bytes UTF-8.')
    from src.infrastructure.security.jwt_service import hash_password
    hashed = hash_password(password)
    engine = create_async_engine(url, echo=False, hide_parameters=True, connect_args={'timeout': 10})
    try:
        async with engine.begin() as conn:
            return await load(conn, data, hashed, seed)
    finally:
        await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Gravar em uma única transação PostgreSQL.')
    parser.add_argument('--seed', type=int, default=200026)
    args = parser.parse_args()
    if sys.flags.optimize:
        parser.error('Execute sem -O: as verificações de consistência são obrigatórias.')
    if business_today() < REFERENCE:
        parser.error('Data local anterior a 08/10/2026; recebimentos futuros não são permitidos.')
    try:
        data = generate(args.seed)
        report = validate_and_report(data, args.seed)
        report['modo'] = 'aplicado' if args.apply else 'simulação sem conexão ao banco'
        if args.apply:
            report['usuario_id'] = asyncio.run(apply(data, args.seed))
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except Exception as exc:
        # SQLAlchemy/asyncpg podem incluir parâmetros ou URL na mensagem original.
        print(f'Carga não concluída ({type(exc).__name__}). Verifique conexão PostgreSQL, migrations, conta já existente e variáveis de ambiente. Nenhum commit parcial é realizado.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
