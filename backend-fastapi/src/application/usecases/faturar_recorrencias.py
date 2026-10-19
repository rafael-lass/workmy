from datetime import date

from src.application.ports.outbound.i_pagamento_repository import IPagamentoRepository
from src.application.ports.outbound.i_projeto_repository import IProjetoRepository
from src.domain.entities.pagamento import PagamentoEntity
from src.domain.entities.projeto import ProjetoEntity
from src.domain.recorrencia import first_due_date, next_month


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
            pagamentos_gerados.extend(await self.execute_projeto(projeto, hoje))

        return pagamentos_gerados

    async def execute_projeto(self, projeto: ProjetoEntity, hoje: date) -> list[PagamentoEntity]:
        """Gera somente vencimentos já alcançados, sem repetir referências existentes."""
        if (projeto.id is None or projeto.valor_mensal is None or
                projeto.tipo_recorrencia != 'MENSAL' or not projeto.recorrencia_ativa or
                projeto.status in {'COMPLETED', 'ARCHIVED'} or projeto.is_deleted):
            return []
        pagamentos_gerados: list[PagamentoEntity] = []
        vencimento = first_due_date(
            projeto.recorrencia_inicio, projeto.dia_vencimento, projeto.criado_em, hoje,
        )
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
            vencimento = next_month(vencimento, projeto.dia_vencimento)
        return pagamentos_gerados
