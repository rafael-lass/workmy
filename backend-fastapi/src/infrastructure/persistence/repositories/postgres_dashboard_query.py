from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ports.outbound.i_dashboard_query import IDashboardQuery
from src.infrastructure.persistence.models import ClienteModel, PagamentoModel, ProjetoModel


def _month_start(value: date) -> date:
    return value.replace(day=1)


def _shift_month(value: date, offset: int) -> date:
    month_index = value.year * 12 + value.month - 1 + offset
    return date(month_index // 12, month_index % 12 + 1, 1)


class PostgresDashboardQuery(IDashboardQuery):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _sum(self, usuario_id: int, *conditions) -> Decimal:
        result = await self.session.execute(
            select(func.coalesce(func.sum(PagamentoModel.valor), Decimal("0.00")))
            .join(ProjetoModel)
            .where(ProjetoModel.usuario_id == usuario_id, *conditions)
        )
        return result.scalar() or Decimal("0.00")

    async def get_resumo(self, usuario_id: int, hoje: date) -> dict:
        current_start = _month_start(hoje)
        next_start = _shift_month(current_start, 1)

        recebido_mes = await self._sum(
            usuario_id,
            PagamentoModel.status == "PAGO",
            PagamentoModel.data_pagamento >= current_start,
            PagamentoModel.data_pagamento < next_start,
        )
        pendente_total = await self._sum(usuario_id, PagamentoModel.status == "PENDENTE")
        atrasado_total = await self._sum(
            usuario_id,
            PagamentoModel.status == "PENDENTE",
            PagamentoModel.data_vencimento < hoje,
        )

        previsto = (
            await self.session.execute(
                select(func.coalesce(func.sum(ProjetoModel.valor_mensal), Decimal("0.00"))).where(
                    ProjetoModel.usuario_id == usuario_id,
                    ProjetoModel.tipo_recorrencia == "MENSAL",
                    ProjetoModel.recorrencia_ativa.is_(True),
                    ProjetoModel.status.notin_(("COMPLETED", "ARCHIVED")),
                    ProjetoModel.deletado_em.is_(None),
                )
            )
        ).scalar() or Decimal("0.00")
        projetos_ativos = (
            await self.session.execute(
                select(func.count(ProjetoModel.id)).where(
                    ProjetoModel.usuario_id == usuario_id,
                    ProjetoModel.status.notin_(("COMPLETED", "ARCHIVED")),
                    ProjetoModel.deletado_em.is_(None),
                )
            )
        ).scalar() or 0
        clientes_total = (
            await self.session.execute(
                select(func.count(ClienteModel.id)).where(
                    ClienteModel.usuario_id == usuario_id,
                    ClienteModel.deletado_em.is_(None),
                )
            )
        ).scalar() or 0

        serie = []
        for offset in range(-5, 1):
            start = _shift_month(current_start, offset)
            end = _shift_month(start, 1)
            total = await self._sum(
                usuario_id,
                PagamentoModel.status == "PAGO",
                PagamentoModel.data_pagamento >= start,
                PagamentoModel.data_pagamento < end,
            )
            serie.append({"mes": start.strftime("%Y-%m"), "total": str(total)})

        return {
            "recebido_mes": str(recebido_mes),
            "pendente_total": str(pendente_total),
            "atrasado_total": str(atrasado_total),
            "previsto_proximo_mes": str(previsto),
            "projetos_ativos": projetos_ativos,
            "clientes_total": clientes_total,
            "serie_seis_meses": serie,
        }
