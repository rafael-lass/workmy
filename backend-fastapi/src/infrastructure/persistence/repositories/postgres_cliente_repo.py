from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.domain.entities.cliente import ClienteEntity
from src.application.ports.outbound.i_cliente_repository import IClienteRepository
from src.infrastructure.persistence.models import ClienteModel

class PostgresClienteRepository(IClienteRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: ClienteModel) -> ClienteEntity:
        return ClienteEntity(
            id=model.id,
            usuario_id=model.usuario_id,
            nome=model.nome,
            empresa=model.empresa,
            email=model.email,
            telefone=model.telefone,
            criado_em=model.criado_em,
            deletado_em=model.deletado_em
        )

    async def get_by_id(self, id: int, usuario_id: int) -> ClienteEntity | None:
        result = await self.session.execute(
            select(ClienteModel).where(
                ClienteModel.id == id,
                ClienteModel.usuario_id == usuario_id,
                ClienteModel.deletado_em.is_(None)
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_usuario(self, usuario_id: int) -> list[ClienteEntity]:
        result = await self.session.execute(
            select(ClienteModel).where(
                ClienteModel.usuario_id == usuario_id,
                ClienteModel.deletado_em.is_(None)
            ).order_by(ClienteModel.criado_em.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def save(self, cliente: ClienteEntity) -> ClienteEntity:
        if cliente.id is None:
            model = ClienteModel(
                usuario_id=cliente.usuario_id,
                nome=cliente.nome,
                empresa=cliente.empresa,
                email=cliente.email,
                telefone=cliente.telefone,
                deletado_em=cliente.deletado_em
            )
            self.session.add(model)
        else:
            result = await self.session.execute(
                select(ClienteModel).where(
                    ClienteModel.id == cliente.id,
                    ClienteModel.usuario_id == cliente.usuario_id
                )
            )
            model = result.scalar_one()
            model.nome = cliente.nome
            model.empresa = cliente.empresa
            model.email = cliente.email
            model.telefone = cliente.telefone
            model.deletado_em = cliente.deletado_em

        await self.session.flush()
        cliente.id = model.id
        cliente.criado_em = model.criado_em
        return cliente

    async def exists_by_id(self, id: int, usuario_id: int) -> bool:
        result = await self.session.execute(
            select(ClienteModel.id).where(
                ClienteModel.id == id,
                ClienteModel.usuario_id == usuario_id,
                ClienteModel.deletado_em.is_(None)
            )
        )
        return result.scalar_one_or_none() is not None

    async def list_with_totals(self, usuario_id: int) -> list['ClienteView']:
        from src.application.dto.views import ClienteView
        from src.infrastructure.persistence.models import PagamentoModel, ProjetoModel
        from sqlalchemy import func
        from decimal import Decimal

        stmt = (
            select(
                ClienteModel.id,
                ClienteModel.nome,
                ClienteModel.empresa,
                ClienteModel.email,
                ClienteModel.telefone,
                ClienteModel.criado_em,
                func.coalesce(func.sum(PagamentoModel.valor), Decimal("0.00")).label("total_acumulado"),
            )
            .select_from(ClienteModel)
            .outerjoin(ProjetoModel, (
                (ProjetoModel.cliente_id == ClienteModel.id) &
                (ProjetoModel.usuario_id == usuario_id) &
                ProjetoModel.deletado_em.is_(None)
            ))
            .outerjoin(PagamentoModel, (
                (PagamentoModel.projeto_id == ProjetoModel.id) &
                (PagamentoModel.status == "PAGO")
            ))
            .where(
                ClienteModel.usuario_id == usuario_id,
                ClienteModel.deletado_em.is_(None),
            )
            .group_by(
                ClienteModel.id,
                ClienteModel.nome,
                ClienteModel.empresa,
                ClienteModel.email,
                ClienteModel.telefone,
                ClienteModel.criado_em,
            )
            .order_by(ClienteModel.nome.asc())
        )

        rows = (await self.session.execute(stmt)).all()
        return [
            ClienteView(
                id=r.id,
                nome=r.nome,
                empresa=r.empresa or "Não informada",
                email=r.email,
                telefone=r.telefone,
                total_acumulado=r.total_acumulado,
                criado_em=r.criado_em,
            )
            for r in rows
        ]

    async def count_projetos_ativos(self, cliente_id: int, usuario_id: int) -> int:
        from src.infrastructure.persistence.models import ProjetoModel
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count(ProjetoModel.id))
            .where(
                ProjetoModel.cliente_id == cliente_id,
                ProjetoModel.usuario_id == usuario_id,
                ProjetoModel.deletado_em.is_(None),
            )
        )
        return result.scalar() or 0

    async def exists_by_name(self, nome: str, usuario_id: int, exclude_id: int | None = None) -> bool:
        stmt = select(ClienteModel.id).where(
            ClienteModel.nome == nome,
            ClienteModel.usuario_id == usuario_id,
            ClienteModel.deletado_em.is_(None)
        )
        if exclude_id is not None:
            stmt = stmt.where(ClienteModel.id != exclude_id)
            
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
