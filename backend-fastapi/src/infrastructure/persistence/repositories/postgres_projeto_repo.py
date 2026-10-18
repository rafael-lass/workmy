from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from sqlalchemy import and_, case, func, select
from sqlalchemy.exc import IntegrityError
from src.domain.entities.projeto import ProjetoEntity
from src.application.ports.outbound.i_projeto_repository import IProjetoRepository
from src.infrastructure.persistence.models import ProjetoModel
from src.domain.exceptions.business_exceptions import ColisaoContratoException

class PostgresProjetoRepository(IProjetoRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: ProjetoModel) -> ProjetoEntity:
        return ProjetoEntity(
            id=model.id,
            usuario_id=model.usuario_id,
            cliente_id=model.cliente_id,
            servico_id=model.servico_id,
            status=model.status,
            data_entrega=model.data_entrega,
            valor=model.valor,
            valor_mensal=model.valor_mensal,
            dia_vencimento=model.dia_vencimento,
            recorrencia_inicio=model.recorrencia_inicio,
            tipo_recorrencia=model.tipo_recorrencia,
            recorrencia_ativa=model.recorrencia_ativa,
            criado_em=model.criado_em,
            deletado_em=model.deletado_em
        )

    async def get_by_id(self, id: int, usuario_id: int) -> ProjetoEntity | None:
        result = await self.session.execute(
            select(ProjetoModel).where(
                ProjetoModel.id == id,
                ProjetoModel.usuario_id == usuario_id,
                ProjetoModel.deletado_em.is_(None)
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_usuario(self, usuario_id: int, cliente_id: int | None = None) -> list[ProjetoEntity]:
        filters = [
            ProjetoModel.usuario_id == usuario_id,
            ProjetoModel.deletado_em.is_(None)
        ]
        if cliente_id is not None:
            filters.append(ProjetoModel.cliente_id == cliente_id)

        result = await self.session.execute(
            select(ProjetoModel).where(and_(*filters)).order_by(ProjetoModel.criado_em.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def save(self, projeto: ProjetoEntity) -> ProjetoEntity:
        if projeto.id is None:
            model = ProjetoModel(
                usuario_id=projeto.usuario_id,
                cliente_id=projeto.cliente_id,
                servico_id=projeto.servico_id,
                status=projeto.status,
                data_entrega=projeto.data_entrega,
                valor=projeto.valor,
                valor_mensal=projeto.valor_mensal,
                dia_vencimento=projeto.dia_vencimento,
                recorrencia_inicio=projeto.recorrencia_inicio,
                tipo_recorrencia=projeto.tipo_recorrencia,
                recorrencia_ativa=projeto.recorrencia_ativa,
                deletado_em=projeto.deletado_em
            )
            try:
                async with self.session.begin_nested():
                    self.session.add(model)
                    await self.session.flush()
            except IntegrityError as exc:
                raise ColisaoContratoException(
                    "Este cliente já possui este serviço contratado de forma ativa."
                ) from exc
        else:
            result = await self.session.execute(
                select(ProjetoModel).where(
                    ProjetoModel.id == projeto.id,
                    ProjetoModel.usuario_id == projeto.usuario_id
                )
            )
            model = result.scalar_one()
            model.status = projeto.status
            model.data_entrega = projeto.data_entrega
            model.valor = projeto.valor
            model.valor_mensal = projeto.valor_mensal
            model.dia_vencimento = projeto.dia_vencimento
            model.recorrencia_inicio = projeto.recorrencia_inicio
            model.tipo_recorrencia = projeto.tipo_recorrencia
            model.recorrencia_ativa = projeto.recorrencia_ativa
            model.deletado_em = projeto.deletado_em

            await self.session.flush()
        projeto.id = model.id
        projeto.criado_em = model.criado_em
        return projeto

    async def exists_active_contract(self, cliente_id: int, servico_id: int, exclude_id: int | None = None) -> bool:
        filters = [
            ProjetoModel.cliente_id == cliente_id,
            ProjetoModel.servico_id == servico_id,
            ProjetoModel.deletado_em.is_(None)
        ]
        if exclude_id is not None:
            filters.append(ProjetoModel.id != exclude_id)

        result = await self.session.execute(
            select(ProjetoModel.id).where(and_(*filters))
        )
        return result.scalar_one_or_none() is not None

    async def list_recorrentes_ativos(self, usuario_id: int) -> list[ProjetoEntity]:
        result = await self.session.execute(
            select(ProjetoModel).where(
                ProjetoModel.usuario_id == usuario_id,
                ProjetoModel.tipo_recorrencia == 'MENSAL',
                ProjetoModel.recorrencia_ativa == True,
                ProjetoModel.status.notin_(("COMPLETED", "ARCHIVED")),
                ProjetoModel.deletado_em.is_(None)
            )
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    def _base_join_query(self, usuario_id: int, cliente_id: int | None = None):
        from src.infrastructure.persistence.models import ClienteModel, PagamentoModel, ServicoModel
        stmt = (
            select(
                ProjetoModel.id,
                ProjetoModel.cliente_id,
                ClienteModel.nome.label("cliente_nome"),
                ProjetoModel.servico_id,
                ServicoModel.nome.label("servico_nome"),
                ProjetoModel.status,
                ProjetoModel.valor,
                ProjetoModel.tipo_recorrencia,
                ProjetoModel.recorrencia_ativa,
                ProjetoModel.valor_mensal,
                ProjetoModel.dia_vencimento,
                ProjetoModel.criado_em.label("data_inicio"),
                ProjetoModel.data_entrega,
                ProjetoModel.recorrencia_inicio,
                ProjetoModel.criado_em,
                func.coalesce(
                    func.sum(
                        case(
                            (PagamentoModel.status == "PAGO", PagamentoModel.valor),
                            else_=Decimal("0.00"),
                        )
                    ),
                    Decimal("0.00"),
                ).label("total_acumulado"),
                (func.count(PagamentoModel.id) > 0).label("possui_lancamentos"),
            )
            .select_from(ProjetoModel)
            .join(ClienteModel, ProjetoModel.cliente_id == ClienteModel.id)
            .join(ServicoModel, ProjetoModel.servico_id == ServicoModel.id)
            .outerjoin(PagamentoModel, PagamentoModel.projeto_id == ProjetoModel.id)
            .where(
                ProjetoModel.usuario_id == usuario_id,
                ProjetoModel.deletado_em.is_(None)
            )
            .group_by(
                ProjetoModel.id,
                ClienteModel.nome,
                ServicoModel.nome,
            )
        )
        if cliente_id is not None:
            stmt = stmt.where(ProjetoModel.cliente_id == cliente_id)
        return stmt

    async def list_with_names(self, usuario_id: int, cliente_id: int | None = None) -> list['ProjetoView']:
        from src.application.dto.views import ProjetoView
        stmt = self._base_join_query(usuario_id, cliente_id)
        rows = (await self.session.execute(stmt)).all()
        return [ProjetoView(**r._mapping) for r in rows]

    async def get_with_names(self, projeto_id: int, usuario_id: int):
        from src.application.dto.views import ProjetoView
        stmt = self._base_join_query(usuario_id).where(ProjetoModel.id == projeto_id)
        row = (await self.session.execute(stmt)).first()
        return ProjetoView(**row._mapping) if row else None

    async def count_lancamentos(self, projeto_id: int) -> int:
        from src.infrastructure.persistence.models import PagamentoModel

        result = await self.session.execute(
            select(func.count(PagamentoModel.id)).where(PagamentoModel.projeto_id == projeto_id)
        )
        return result.scalar() or 0
