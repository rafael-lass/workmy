from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.views import PagamentoView
from src.application.ports.outbound.i_pagamento_repository import IPagamentoRepository
from src.domain.entities.pagamento import PagamentoEntity
from src.infrastructure.persistence.models import (
    ClienteModel,
    PagamentoModel,
    ProjetoModel,
    ServicoModel,
)


class PostgresPagamentoRepository(IPagamentoRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _to_entity(model: PagamentoModel) -> PagamentoEntity:
        return PagamentoEntity(
            id=model.id,
            projeto_id=model.projeto_id,
            valor=model.valor,
            tipo_pagamento=model.tipo_pagamento,
            status=model.status,
            data_vencimento=model.data_vencimento,
            data_pagamento=model.data_pagamento,
            observacao=model.observacao,
            referencia_mes=model.referencia_mes,
            gerado_automaticamente=model.gerado_automaticamente,
            comprovante_bytes=model.comprovante_bytes,
            comprovante_mime=model.comprovante_mime,
            status_alterado_em=model.status_alterado_em,
            motivo_ajuste=model.motivo_ajuste,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
        )

    async def get_by_id(self, id: int, usuario_id: int) -> PagamentoEntity | None:
        result = await self.session.execute(
            select(PagamentoModel)
            .join(ProjetoModel)
            .where(PagamentoModel.id == id, ProjetoModel.usuario_id == usuario_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, pagamento: PagamentoEntity) -> PagamentoEntity:
        if pagamento.id is None:
            model = PagamentoModel(projeto_id=pagamento.projeto_id, valor=pagamento.valor)
            self.session.add(model)
        else:
            model = (
                await self.session.execute(
                    select(PagamentoModel).where(PagamentoModel.id == pagamento.id)
                )
            ).scalar_one()

        model.projeto_id = pagamento.projeto_id
        model.valor = pagamento.valor
        model.tipo_pagamento = pagamento.tipo_pagamento
        model.status = pagamento.status
        model.data_vencimento = pagamento.data_vencimento
        model.data_pagamento = pagamento.data_pagamento
        model.observacao = pagamento.observacao
        model.referencia_mes = pagamento.referencia_mes
        model.gerado_automaticamente = pagamento.gerado_automaticamente
        model.status_alterado_em = pagamento.status_alterado_em
        model.motivo_ajuste = pagamento.motivo_ajuste
        model.comprovante_bytes = pagamento.comprovante_bytes
        model.comprovante_mime = pagamento.comprovante_mime

        await self.session.flush()
        pagamento.id = model.id
        pagamento.criado_em = model.criado_em
        pagamento.atualizado_em = model.atualizado_em
        return pagamento

    async def save_recorrencia(self, pagamento: PagamentoEntity) -> PagamentoEntity | None:
        if pagamento.referencia_mes is None:
            raise ValueError("Uma recorrência exige referência mensal.")

        existing = (
            await self.session.execute(
                select(PagamentoModel).where(
                    PagamentoModel.projeto_id == pagamento.projeto_id,
                    PagamentoModel.referencia_mes == pagamento.referencia_mes,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return None

        model = PagamentoModel(
            projeto_id=pagamento.projeto_id,
            valor=pagamento.valor,
            tipo_pagamento=pagamento.tipo_pagamento,
            status=pagamento.status,
            data_vencimento=pagamento.data_vencimento,
            data_pagamento=pagamento.data_pagamento,
            observacao=pagamento.observacao,
            referencia_mes=pagamento.referencia_mes,
            gerado_automaticamente=True,
            comprovante_bytes=pagamento.comprovante_bytes,
            comprovante_mime=pagamento.comprovante_mime,
        )
        try:
            async with self.session.begin_nested():
                self.session.add(model)
                await self.session.flush()
        except IntegrityError:
            return None

        return self._to_entity(model)

    async def list_with_names(
        self,
        usuario_id: int,
        filters: dict,
        page: int,
        page_size: int,
    ) -> tuple[list[PagamentoView], int]:
        conditions = [ProjetoModel.usuario_id == usuario_id]
        if filters.get("status"):
            conditions.append(PagamentoModel.status == filters["status"])
        if filters.get("tipo_pagamento"):
            conditions.append(PagamentoModel.tipo_pagamento == filters["tipo_pagamento"])
        if filters.get("cliente_id"):
            conditions.append(ProjetoModel.cliente_id == filters["cliente_id"])
        if filters.get("projeto_id"):
            conditions.append(PagamentoModel.projeto_id == filters["projeto_id"])
        if filters.get("data_inicio"):
            conditions.append(PagamentoModel.data_vencimento >= filters["data_inicio"])
        if filters.get("data_fim"):
            conditions.append(PagamentoModel.data_vencimento <= filters["data_fim"])
        if filters.get("q"):
            term = f"%{filters['q'].strip().lower()}%"
            conditions.append(
                or_(
                    func.lower(ClienteModel.nome).like(term),
                    func.lower(ServicoModel.nome).like(term),
                    func.lower(func.coalesce(PagamentoModel.observacao, "")).like(term),
                )
            )

        base = (
            select(PagamentoModel.id)
            .select_from(PagamentoModel)
            .join(ProjetoModel, PagamentoModel.projeto_id == ProjetoModel.id)
            .join(ClienteModel, ProjetoModel.cliente_id == ClienteModel.id)
            .join(ServicoModel, ProjetoModel.servico_id == ServicoModel.id)
            .where(*conditions)
        )
        total = (
            await self.session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()

        stmt = (
            select(
                PagamentoModel.id,
                PagamentoModel.projeto_id,
                ProjetoModel.cliente_id,
                ClienteModel.nome.label("cliente_nome"),
                ServicoModel.nome.label("servico_nome"),
                PagamentoModel.valor,
                PagamentoModel.tipo_pagamento,
                PagamentoModel.status,
                PagamentoModel.data_vencimento,
                PagamentoModel.data_pagamento,
                PagamentoModel.referencia_mes,
                PagamentoModel.gerado_automaticamente,
                PagamentoModel.criado_em,
                PagamentoModel.atualizado_em,
                PagamentoModel.status_alterado_em,
                PagamentoModel.motivo_ajuste,
                PagamentoModel.observacao,
                PagamentoModel.comprovante_bytes,
                PagamentoModel.comprovante_mime,
            )
            .select_from(PagamentoModel)
            .join(ProjetoModel, PagamentoModel.projeto_id == ProjetoModel.id)
            .join(ClienteModel, ProjetoModel.cliente_id == ClienteModel.id)
            .join(ServicoModel, ProjetoModel.servico_id == ServicoModel.id)
            .where(*conditions)
            .order_by(PagamentoModel.data_vencimento.desc(), PagamentoModel.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.session.execute(stmt)).all()
        return [PagamentoView(**row._mapping) for row in rows], total
