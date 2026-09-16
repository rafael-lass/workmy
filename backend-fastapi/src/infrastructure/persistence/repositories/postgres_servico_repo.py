from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from src.domain.entities.servico import ServicoEntity
from src.domain.exceptions.business_exceptions import ValidaEntidadeException
from src.application.ports.outbound.i_servico_repository import IServicoRepository
from src.infrastructure.persistence.models import ServicoModel, TagModel

class PostgresServicoRepository(IServicoRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: ServicoModel) -> ServicoEntity:
        return ServicoEntity(
            id=model.id,
            usuario_id=model.usuario_id,
            nome=model.nome,
            descricao=model.descricao,
            descricao_documento=model.descricao_documento,
            etiquetas=[{"id": tag.id, "nome": tag.nome} for tag in model.etiquetas],
            tags=model.tags,
            ferramentas=model.ferramentas,
            github_repo=model.github_repo,
            imagem_bytes=model.imagem_bytes,
            imagem_mime=model.imagem_mime,
            criado_em=model.criado_em,
            deletado_em=model.deletado_em
        )

    async def get_by_id(self, id: int, usuario_id: int) -> ServicoEntity | None:
        result = await self.session.execute(
            select(ServicoModel).where(
                ServicoModel.id == id,
                ServicoModel.usuario_id == usuario_id,
                ServicoModel.deletado_em.is_(None)
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_usuario(self, usuario_id: int) -> list[ServicoEntity]:
        result = await self.session.execute(
            select(ServicoModel).where(
                ServicoModel.usuario_id == usuario_id,
                ServicoModel.deletado_em.is_(None)
            ).order_by(ServicoModel.criado_em.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def save(self, servico: ServicoEntity) -> ServicoEntity:
        tag_ids = [tag["id"] for tag in servico.etiquetas]
        etiquetas = (await self.session.execute(select(TagModel).where(
            TagModel.id.in_(tag_ids), TagModel.usuario_id == servico.usuario_id
        ))).scalars().all()
        if len(etiquetas) != len(set(tag_ids)):
            raise ValidaEntidadeException("Uma ou mais tags não pertencem ao seu catálogo.")
        if servico.id is None:
            try:
                async with self.session.begin_nested():
                    model = ServicoModel(
                        usuario_id=servico.usuario_id,
                        nome=servico.nome,
                        descricao=servico.descricao,
                        descricao_documento=servico.descricao_documento,
                        etiquetas=etiquetas,
                        tags=servico.tags,
                        ferramentas=servico.ferramentas,
                        github_repo=servico.github_repo,
                        imagem_bytes=servico.imagem_bytes,
                        imagem_mime=servico.imagem_mime,
                        deletado_em=servico.deletado_em
                    )
                    self.session.add(model)
                    await self.session.flush()
            except IntegrityError as exc:
                raise ValidaEntidadeException(
                    "Já existe um serviço com este nome."
                ) from exc
        else:
            result = await self.session.execute(
                select(ServicoModel).where(
                    ServicoModel.id == servico.id,
                    ServicoModel.usuario_id == servico.usuario_id
                )
            )
            model = result.scalar_one()
            try:
                async with self.session.begin_nested():
                    model.nome = servico.nome
                    model.descricao = servico.descricao
                    model.descricao_documento = servico.descricao_documento
                    model.etiquetas = etiquetas
                    model.tags = servico.tags
                    model.ferramentas = servico.ferramentas
                    model.github_repo = servico.github_repo
                    model.imagem_bytes = servico.imagem_bytes
                    model.imagem_mime = servico.imagem_mime
                    model.deletado_em = servico.deletado_em
                    await self.session.flush()
            except IntegrityError as exc:
                raise ValidaEntidadeException(
                    "Já existe um serviço com este nome."
                ) from exc

        servico.id = model.id
        servico.criado_em = model.criado_em
        servico.etiquetas = [{"id": tag.id, "nome": tag.nome} for tag in etiquetas]
        return servico

    async def list_tags(self, usuario_id: int) -> list[dict]:
        rows = (await self.session.execute(select(TagModel).where(
            TagModel.usuario_id == usuario_id
        ).order_by(TagModel.nome_normalizado))).scalars().all()
        return [{"id": tag.id, "nome": tag.nome} for tag in rows]

    async def create_tag(self, usuario_id: int, nome: str) -> dict:
        nome = " ".join(nome.split())
        if not nome or len(nome) > 40:
            raise ValidaEntidadeException("A tag deve ter entre 1 e 40 caracteres.")
        query = select(TagModel).where(TagModel.usuario_id == usuario_id, TagModel.nome_normalizado == nome.casefold())
        tag = (await self.session.execute(query)).scalar_one_or_none()
        if tag is None:
            try:
                async with self.session.begin_nested():
                    tag = TagModel(usuario_id=usuario_id, nome=nome, nome_normalizado=nome.casefold())
                    self.session.add(tag)
                    await self.session.flush()
            except IntegrityError:
                tag = (await self.session.execute(query)).scalar_one()
        return {"id": tag.id, "nome": tag.nome}

    async def exists_by_id(self, id: int, usuario_id: int) -> bool:
        result = await self.session.execute(
            select(ServicoModel.id).where(
                ServicoModel.id == id,
                ServicoModel.usuario_id == usuario_id,
                ServicoModel.deletado_em.is_(None)
            )
        )
        return result.scalar_one_or_none() is not None

    async def count_projetos_ativos(self, servico_id: int, usuario_id: int) -> int:
        from src.infrastructure.persistence.models import ProjetoModel
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count(ProjetoModel.id))
            .where(
                ProjetoModel.servico_id == servico_id,
                ProjetoModel.usuario_id == usuario_id,
                ProjetoModel.deletado_em.is_(None),
            )
        )
        return result.scalar() or 0

    async def exists_by_name(self, nome: str, usuario_id: int, exclude_id: int | None = None) -> bool:
        stmt = select(ServicoModel.id).where(
            ServicoModel.nome == nome,
            ServicoModel.usuario_id == usuario_id,
            ServicoModel.deletado_em.is_(None)
        )
        if exclude_id is not None:
            stmt = stmt.where(ServicoModel.id != exclude_id)
            
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
