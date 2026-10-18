from contextlib import asynccontextmanager
from sqlalchemy import select
from src.infrastructure.persistence.models import ClienteModel as C, ServicoModel as S, ProjetoModel as P, PagamentoModel as M


class PostgresExcelQuery:
    """Projeções sem entidades ORM, em uma sessão e snapshot consistente."""
    def __init__(self, session):
        self.session = session

    @asynccontextmanager
    async def snapshot(self):
        try:
            if self.session.get_bind().dialect.name == 'postgresql':
                await self.session.connection(execution_options={'isolation_level': 'REPEATABLE READ'})
            yield
        finally:
            await self.session.rollback()

    def payment_filter(self, period):
        return [] if period.start is None else [M.data_vencimento >= period.start, M.data_vencimento <= period.today]

    def project_ids(self, user_id, period):
        return select(M.projeto_id).join(P, P.id == M.projeto_id).where(P.usuario_id == user_id, *self.payment_filter(period))

    def selected_projects(self, user_id, period):
        query = select(P.id).where(P.usuario_id == user_id)
        return query if period.start is None else query.where(P.id.in_(self.project_ids(user_id, period)))

    async def rows(self, query):
        return [dict(row) for row in (await self.session.execute(query)).mappings()]

    async def payments(self, user_id, period):
        return await self.rows(select(M.id, M.projeto_id, P.cliente_id, C.nome.label('cliente'), P.servico_id,
            S.nome.label('servico'), M.tipo_pagamento, M.status, M.referencia_mes, M.data_vencimento,
            M.data_pagamento, M.valor, M.observacao, M.motivo_ajuste, M.criado_em,
            M.atualizado_em).join(P, P.id == M.projeto_id).join(C, C.id == P.cliente_id).join(S, S.id == P.servico_id)
            .where(P.usuario_id == user_id, C.usuario_id == user_id, S.usuario_id == user_id,
                   *self.payment_filter(period)).order_by(M.data_vencimento, M.id))

    async def projects(self, user_id, period):
        return await self.rows(select(P.id, P.cliente_id, C.nome.label('cliente'), P.servico_id,
            S.nome.label('servico'), P.status, P.tipo_recorrencia, P.recorrencia_ativa, P.valor,
            P.valor_mensal, P.dia_vencimento, P.recorrencia_inicio, P.data_entrega, P.criado_em,
            P.deletado_em).join(C, C.id == P.cliente_id).join(S, S.id == P.servico_id)
            .where(P.id.in_(self.selected_projects(user_id, period)), C.usuario_id == user_id,
                   S.usuario_id == user_id).order_by(P.id))

    async def clients(self, user_id, period):
        query = select(C.id, C.nome, C.empresa, C.email, C.telefone, C.criado_em, C.deletado_em).where(C.usuario_id == user_id)
        if period.start is not None:
            query = query.where(C.id.in_(select(P.cliente_id).where(P.id.in_(self.selected_projects(user_id, period)))))
        return await self.rows(query.order_by(C.id))

    async def services(self, user_id, period):
        query = select(S.id, S.nome, S.descricao_documento, S.descricao, S.criado_em, S.deletado_em).where(S.usuario_id == user_id)
        if period.start is not None:
            query = query.where(S.id.in_(select(P.servico_id).where(P.id.in_(self.selected_projects(user_id, period)))))
        return await self.rows(query.order_by(S.id))
