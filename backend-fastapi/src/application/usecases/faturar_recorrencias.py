from datetime import date

from src.application.ports.outbound.i_pagamento_repository import IPagamentoRepository
from src.application.ports.outbound.i_projeto_repository import IProjetoRepository
from src.domain.entities.pagamento import PagamentoEntity


def _next_month(value: date, due_day: int) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, due_day)
    return date(value.year, value.month + 1, due_day)


def _first_due_date(start: date, due_day: int) -> date:
    candidate = date(start.year, start.month, due_day)
    return candidate if candidate >= start else _next_month(candidate, due_day)


class FaturarRecorrenciasUseCase:
    def __init__(
        self,
        projeto_repo: IProjetoRepository,
        pagamento_repo: IPagamentoRepository,
    ):
        self.projeto_repo = projeto_repo
        self.pagamento_repo = pagamento_repo

    async def execute(self, usuario_id: int, hoje: date) -> list[PagamentoEntity]:
        pagamentos_gerados: list[PagamentoEntity] = []
        projetos = await self.projeto_repo.list_recorrentes_ativos(usuario_id)

        for projeto in projetos:
            if projeto.id is None or projeto.valor_mensal is None:
                continue
            start = projeto.recorrencia_inicio
            if start is None:
                start = projeto.criado_em.date() if projeto.criado_em else hoje

            vencimento = _first_due_date(start, projeto.dia_vencimento)
            while vencimento <= hoje:
                pagamento = PagamentoEntity(
                    projeto_id=projeto.id,
                    valor=projeto.valor_mensal,
                    tipo_pagamento="MENSAL",
                    status="PENDENTE",
                    data_vencimento=vencimento,
                    data_pagamento=None,
                    referencia_mes=vencimento.strftime("%Y-%m"),
                    gerado_automaticamente=True,
                    observacao="Gerado pela recorrência mensal",
                )
                pagamento.validate()
                salvo = await self.pagamento_repo.save_recorrencia(pagamento)
                if salvo is not None:
                    pagamentos_gerados.append(salvo)
                vencimento = _next_month(vencimento, projeto.dia_vencimento)

        return pagamentos_gerados
