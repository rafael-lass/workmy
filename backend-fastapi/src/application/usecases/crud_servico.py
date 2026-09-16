import datetime as dt
from typing import Optional
from src.domain.entities.servico import ServicoEntity
from src.domain.exceptions.business_exceptions import (
    ValidaEntidadeException, NaoEncontradoException, ConflitoDeletarException
)
from src.application.ports.outbound.i_servico_repository import IServicoRepository

class CrudServicoUseCase:
    def __init__(self, servico_repo: IServicoRepository):
        self.servico_repo = servico_repo

    async def criar(
        self,
        usuario_id: int,
        nome: str,
        descricao: Optional[str] = None,
        tags: Optional[str] = None,
        ferramentas: Optional[str] = None,
        github_repo: Optional[str] = None,
        imagem_bytes: Optional[bytes] = None,
        imagem_mime: Optional[str] = None,
        descricao_documento: dict | None = None,
        tag_ids: list[int] | None = None,
    ) -> ServicoEntity:
        # 1. Verifica nome único
        if await self.servico_repo.exists_by_name(nome, usuario_id):
            raise ValidaEntidadeException("Já existe um serviço com este nome.")

        # 2. Cria Entidade e Valida
        servico = ServicoEntity(
            usuario_id=usuario_id,
            nome=nome,
            descricao=descricao,
            tags=tags,
            ferramentas=ferramentas,
            github_repo=github_repo,
            imagem_bytes=imagem_bytes,
            imagem_mime=imagem_mime
        )
        from src.domain.service_document import validate_document
        servico.descricao_documento = validate_document(descricao_documento)
        servico.etiquetas = [{"id": id} for id in dict.fromkeys(tag_ids or [])]
        servico.validate()

        # 3. Salva
        return await self.servico_repo.save(servico)

    async def atualizar(
        self,
        servico_id: int,
        usuario_id: int,
        nome: str,
        descricao: Optional[str] = None,
        tags: Optional[str] = None,
        ferramentas: Optional[str] = None,
        github_repo: Optional[str] = None,
        imagem_bytes: Optional[bytes] = None,
        imagem_mime: Optional[str] = None,
        descricao_documento: dict | None = None,
        tag_ids: list[int] | None = None,
    ) -> ServicoEntity:
        # 1. Recupera
        servico = await self.servico_repo.get_by_id(servico_id, usuario_id)
        if not servico:
            raise NaoEncontradoException("Serviço não encontrado.")

        # 2. Verifica nome único (excluindo ele mesmo)
        if await self.servico_repo.exists_by_name(nome, usuario_id, exclude_id=servico_id):
            raise ValidaEntidadeException("Já existe um outro serviço com este nome.")

        # 3. Atualiza
        servico.nome = nome
        # Legacy columns are retained without overwriting previously saved data.
        from src.domain.service_document import validate_document
        servico.descricao_documento = validate_document(descricao_documento)
        servico.etiquetas = [{"id": id} for id in dict.fromkeys(tag_ids or [])]
        
        # Só atualiza a imagem se uma nova for enviada
        if imagem_bytes is not None:
            servico.imagem_bytes = imagem_bytes
            servico.imagem_mime = imagem_mime

        servico.validate()

        # 4. Salva
        return await self.servico_repo.save(servico)

    async def deletar(self, servico_id: int, usuario_id: int) -> None:
        # 1. Recupera
        servico = await self.servico_repo.get_by_id(servico_id, usuario_id)
        if not servico:
            raise NaoEncontradoException("Serviço não encontrado.")

        # 2. Verifica dependências
        projetos_ativos = await self.servico_repo.count_projetos_ativos(servico_id, usuario_id)
        if projetos_ativos > 0:
            raise ConflitoDeletarException(
                f"Não é possível deletar serviço com {projetos_ativos} projeto(s) associado(s)."
            )

        # 3. Deleta (Soft Delete)
        servico.deletado_em = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
        await self.servico_repo.save(servico)
