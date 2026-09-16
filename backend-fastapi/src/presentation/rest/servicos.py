from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Response
from starlette.concurrency import run_in_threadpool
import re

from src.application.ports.outbound.i_servico_repository import IServicoRepository
from src.application.usecases.crud_servico import CrudServicoUseCase
from src.domain.entities.servico import ServicoEntity
from src.domain.exceptions.business_exceptions import (
    ConflitoDeletarException,
    NaoEncontradoException,
    ValidaEntidadeException,
)
from src.presentation.dependencies import get_crud_servico_usecase, get_servico_repository
from src.presentation.dto.schemas import MessageSchema, ServicoInSchema, ServicoOutSchema, TagInSchema, TagOutSchema, ServicoPdfSchema
from src.domain.service_document import plain_text
from src.presentation.file_utils import decode_image_data_url, encode_data_url
from src.presentation.middleware.auth import get_current_user_id

router = APIRouter(prefix="/servicos", tags=["Serviços"])


def _to_dict(servico: ServicoEntity) -> dict:
    return {
        "id": servico.id,
        "nome": servico.nome,
        "descricao_documento": servico.descricao_documento,
        "descricao_resumo": plain_text((servico.descricao_documento or {}).get("doc"))[:240],
        "tags": servico.etiquetas,
        "imagem_base64": encode_data_url(servico.imagem_bytes, servico.imagem_mime),
        "criado_em": servico.criado_em.isoformat() if servico.criado_em else "",
    }


@router.get("/", response_model=List[ServicoOutSchema])
async def list_servicos(
    usuario_id: int = Depends(get_current_user_id),
    repo: IServicoRepository = Depends(get_servico_repository),
):
    return [_to_dict(servico) for servico in await repo.list_by_usuario(usuario_id)]


@router.get("/tags", response_model=list[TagOutSchema])
async def list_tags(usuario_id: int = Depends(get_current_user_id), repo: IServicoRepository = Depends(get_servico_repository)):
    return await repo.list_tags(usuario_id)


@router.post("/tags", response_model=TagOutSchema)
async def create_tag(payload: TagInSchema, usuario_id: int = Depends(get_current_user_id), repo: IServicoRepository = Depends(get_servico_repository)):
    try:
        return await repo.create_tag(usuario_id, payload.nome)
    except ValidaEntidadeException as exc:
        raise HTTPException(400, detail=str(exc)) from exc


@router.post("/{servico_id}/pdf")
async def export_pdf(servico_id: int, payload: ServicoPdfSchema, usuario_id: int = Depends(get_current_user_id), repo: IServicoRepository = Depends(get_servico_repository)):
    from src.application.usecases.exportar_servico import ExportarServicoUseCase
    from src.infrastructure.documents.service_pdf import ServicePdfRenderer
    try:
        service, contact = await ExportarServicoUseCase(repo).preparar(servico_id, usuario_id, payload.model_dump())
    except NaoEncontradoException as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    pdf = await run_in_threadpool(ServicePdfRenderer().render, service, contact)
    filename = re.sub(r"[^a-zA-Z0-9_-]", "-", service.nome).strip("-")[:80] or "servico"
    return Response(pdf, media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="{filename}.pdf"',
        "Cache-Control": "no-store",
    })


@router.get("/{servico_id}", response_model=ServicoOutSchema)
async def get_servico(
    servico_id: int,
    usuario_id: int = Depends(get_current_user_id),
    repo: IServicoRepository = Depends(get_servico_repository),
):
    servico = await repo.get_by_id(servico_id, usuario_id)
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado.")
    return _to_dict(servico)


@router.post("/", response_model=ServicoOutSchema, status_code=status.HTTP_201_CREATED)
async def create_servico(
    payload: ServicoInSchema,
    usuario_id: int = Depends(get_current_user_id),
    use_case: CrudServicoUseCase = Depends(get_crud_servico_usecase),
):
    try:
        imagem_bytes, imagem_mime = decode_image_data_url(payload.imagem_base64)
        servico = await use_case.criar(
            usuario_id=usuario_id,
            nome=payload.nome,
            descricao_documento=payload.descricao_documento,
            tag_ids=payload.tag_ids,
            imagem_bytes=imagem_bytes,
            imagem_mime=imagem_mime,
        )
        return _to_dict(servico)
    except (ValidaEntidadeException, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{servico_id}", response_model=ServicoOutSchema)
async def update_servico(
    servico_id: int,
    payload: ServicoInSchema,
    usuario_id: int = Depends(get_current_user_id),
    use_case: CrudServicoUseCase = Depends(get_crud_servico_usecase),
):
    try:
        imagem_bytes, imagem_mime = decode_image_data_url(payload.imagem_base64)
        servico = await use_case.atualizar(
            servico_id=servico_id,
            usuario_id=usuario_id,
            nome=payload.nome,
            descricao_documento=payload.descricao_documento,
            tag_ids=payload.tag_ids,
            imagem_bytes=imagem_bytes,
            imagem_mime=imagem_mime,
        )
        return _to_dict(servico)
    except NaoEncontradoException as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValidaEntidadeException, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{servico_id}", response_model=MessageSchema)
async def delete_servico(
    servico_id: int,
    usuario_id: int = Depends(get_current_user_id),
    use_case: CrudServicoUseCase = Depends(get_crud_servico_usecase),
):
    try:
        await use_case.deletar(servico_id, usuario_id)
        return {"message": "Serviço excluído com sucesso."}
    except NaoEncontradoException as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ConflitoDeletarException as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
