from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from src.application.dto.views import PagamentoView
from src.application.ports.outbound.i_pagamento_repository import IPagamentoRepository
from src.application.ports.outbound.i_projeto_repository import IProjetoRepository
from src.application.usecases.crud_pagamento import CrudPagamentoUseCase
from src.domain.entities.pagamento import PagamentoEntity
from src.domain.exceptions.business_exceptions import NaoEncontradoException, ValidaEntidadeException
from src.domain.time import business_today
from src.presentation.dependencies import (
    get_crud_pagamento_usecase,
    get_pagamento_repository,
    get_projeto_repository,
)
from src.presentation.dto.schemas import (
    AjustePagamentoSchema,
    PagamentoDetalhesSchema,
    PagamentoInSchema,
    PagamentoListOutSchema,
    PagamentoOutSchema,
    ReceberPagamentoSchema,
)
from src.presentation.file_utils import decode_receipt_data_url, encode_data_url
from src.presentation.middleware.auth import get_current_user_id


router = APIRouter(prefix="/pagamentos", tags=["Financeiro"])


def pagamento_view_to_dict(view: PagamentoView) -> dict:
    return {
        "id": view.id,
        "projeto_id": view.projeto_id,
        "cliente_id": view.cliente_id,
        "projeto_cliente_nome": view.cliente_nome,
        "projeto_servico_nome": view.servico_nome,
        "valor": str(view.valor),
        "tipo_pagamento": view.tipo_pagamento,
        "tipo_pagamento_display": "Mensalidade" if view.tipo_pagamento == "MENSAL" else "Avulso",
        "status": view.status,
        "em_atraso": view.status == "PENDENTE" and view.data_vencimento < business_today(),
        "data_vencimento": view.data_vencimento.isoformat(),
        "data_pagamento": view.data_pagamento.isoformat() if view.data_pagamento else None,
        "referencia_mes": view.referencia_mes,
        "gerado_automaticamente": view.gerado_automaticamente,
        "observacao": view.observacao,
        "comprovante_base64": encode_data_url(view.comprovante_bytes, view.comprovante_mime),
        "motivo_ajuste": view.motivo_ajuste,
        "status_alterado_em": view.status_alterado_em.isoformat(),
        "criado_em": view.criado_em.isoformat(),
        "atualizado_em": view.atualizado_em.isoformat(),
    }


def pagamento_entity_to_dict(pagamento: PagamentoEntity, projeto_view) -> dict:
    return {
        "id": pagamento.id,
        "projeto_id": pagamento.projeto_id,
        "cliente_id": projeto_view.cliente_id,
        "projeto_cliente_nome": projeto_view.cliente_nome,
        "projeto_servico_nome": projeto_view.servico_nome,
        "valor": str(pagamento.valor),
        "tipo_pagamento": pagamento.tipo_pagamento,
        "tipo_pagamento_display": "Mensalidade" if pagamento.tipo_pagamento == "MENSAL" else "Avulso",
        "status": pagamento.status,
        "em_atraso": pagamento.em_atraso(),
        "data_vencimento": pagamento.data_vencimento.isoformat(),
        "data_pagamento": pagamento.data_pagamento.isoformat() if pagamento.data_pagamento else None,
        "referencia_mes": pagamento.referencia_mes,
        "gerado_automaticamente": pagamento.gerado_automaticamente,
        "observacao": pagamento.observacao,
        "comprovante_base64": encode_data_url(
            pagamento.comprovante_bytes, pagamento.comprovante_mime
        ),
        "motivo_ajuste": pagamento.motivo_ajuste,
        "status_alterado_em": pagamento.status_alterado_em.isoformat(),
        "criado_em": (pagamento.criado_em or pagamento.status_alterado_em).isoformat(),
        "atualizado_em": (pagamento.atualizado_em or pagamento.status_alterado_em).isoformat(),
    }


async def _serialize_entity(
    pagamento: PagamentoEntity,
    usuario_id: int,
    projeto_repo: IProjetoRepository,
) -> dict:
    projeto = await projeto_repo.get_with_names(pagamento.projeto_id, usuario_id)
    if projeto is None:
        raise HTTPException(status_code=404, detail="Projeto do lançamento não encontrado.")
    return pagamento_entity_to_dict(pagamento, projeto)


@router.get("/", response_model=PagamentoListOutSchema)
async def list_pagamentos(
    status: Literal["PENDENTE", "PAGO", "CANCELADO", "ESTORNADO"] | None = None,
    tipo_pagamento: Literal["MENSAL", "AVULSO"] | None = None,
    cliente_id: int | None = Query(None, ge=1),
    projeto_id: int | None = Query(None, ge=1),
    data_inicio: date | None = None,
    data_fim: date | None = None,
    q: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    usuario_id: int = Depends(get_current_user_id),
    repo: IPagamentoRepository = Depends(get_pagamento_repository),
):
    if data_inicio and data_fim and data_inicio > data_fim:
        raise HTTPException(status_code=400, detail="A data inicial não pode superar a data final.")
    items, total = await repo.list_with_names(
        usuario_id,
        {
            "status": status,
            "tipo_pagamento": tipo_pagamento,
            "cliente_id": cliente_id,
            "projeto_id": projeto_id,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "q": q,
        },
        page,
        page_size,
    )
    return {
        "items": [pagamento_view_to_dict(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/", response_model=PagamentoOutSchema, status_code=201)
async def create_pagamento(
    payload: PagamentoInSchema,
    usuario_id: int = Depends(get_current_user_id),
    use_case: CrudPagamentoUseCase = Depends(get_crud_pagamento_usecase),
    projeto_repo: IProjetoRepository = Depends(get_projeto_repository),
):
    try:
        comp_bytes, comp_mime = decode_receipt_data_url(payload.comprovante_base64)
        pagamento = await use_case.criar(
            projeto_id=payload.projeto_id,
            usuario_id=usuario_id,
            valor=payload.valor,
            data_pagamento=payload.data_pagamento,
            observacao=payload.observacao,
            comprovante_bytes=comp_bytes,
            comprovante_mime=comp_mime,
        )
        return await _serialize_entity(pagamento, usuario_id, projeto_repo)
    except NaoEncontradoException as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValidaEntidadeException, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{pagamento_id}/receber", response_model=PagamentoOutSchema)
async def receber_pagamento(
    pagamento_id: int,
    payload: ReceberPagamentoSchema,
    usuario_id: int = Depends(get_current_user_id),
    use_case: CrudPagamentoUseCase = Depends(get_crud_pagamento_usecase),
    projeto_repo: IProjetoRepository = Depends(get_projeto_repository),
):
    try:
        comp_bytes, comp_mime = decode_receipt_data_url(payload.comprovante_base64)
        pagamento = await use_case.receber(
            pagamento_id,
            usuario_id,
            payload.data_pagamento,
            payload.observacao,
            comp_bytes,
            comp_mime,
        )
        return await _serialize_entity(pagamento, usuario_id, projeto_repo)
    except NaoEncontradoException as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValidaEntidadeException, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


async def _change_status(
    pagamento_id: int,
    usuario_id: int,
    motivo: str,
    action: str,
    use_case: CrudPagamentoUseCase,
    projeto_repo: IProjetoRepository,
) -> dict:
    try:
        pagamento = (
            await use_case.cancelar(pagamento_id, usuario_id, motivo)
            if action == "cancelar"
            else await use_case.estornar(pagamento_id, usuario_id, motivo)
        )
        return await _serialize_entity(pagamento, usuario_id, projeto_repo)
    except NaoEncontradoException as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidaEntidadeException as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{pagamento_id}/cancelar", response_model=PagamentoOutSchema)
async def cancelar_pagamento(
    pagamento_id: int,
    payload: AjustePagamentoSchema,
    usuario_id: int = Depends(get_current_user_id),
    use_case: CrudPagamentoUseCase = Depends(get_crud_pagamento_usecase),
    projeto_repo: IProjetoRepository = Depends(get_projeto_repository),
):
    return await _change_status(
        pagamento_id, usuario_id, payload.motivo, "cancelar", use_case, projeto_repo
    )


@router.patch("/{pagamento_id}/estornar", response_model=PagamentoOutSchema)
async def estornar_pagamento(
    pagamento_id: int,
    payload: AjustePagamentoSchema,
    usuario_id: int = Depends(get_current_user_id),
    use_case: CrudPagamentoUseCase = Depends(get_crud_pagamento_usecase),
    projeto_repo: IProjetoRepository = Depends(get_projeto_repository),
):
    return await _change_status(
        pagamento_id, usuario_id, payload.motivo, "estornar", use_case, projeto_repo
    )


@router.patch("/{pagamento_id}/detalhes", response_model=PagamentoOutSchema)
async def atualizar_detalhes_pagamento(
    pagamento_id: int,
    payload: PagamentoDetalhesSchema,
    usuario_id: int = Depends(get_current_user_id),
    use_case: CrudPagamentoUseCase = Depends(get_crud_pagamento_usecase),
    pagamento_repo: IPagamentoRepository = Depends(get_pagamento_repository),
    projeto_repo: IProjetoRepository = Depends(get_projeto_repository),
):
    try:
        current = await pagamento_repo.get_by_id(pagamento_id, usuario_id)
        if current is None:
            raise NaoEncontradoException("Lançamento financeiro não encontrado.")
        raw = payload.model_dump(exclude_unset=True)
        comp_bytes = current.comprovante_bytes
        comp_mime = current.comprovante_mime
        if "comprovante_base64" in raw:
            comp_bytes, comp_mime = decode_receipt_data_url(raw["comprovante_base64"])
        pagamento = await use_case.atualizar_detalhes(
            pagamento_id,
            usuario_id,
            raw.get("observacao", current.observacao),
            comp_bytes,
            comp_mime,
        )
        return await _serialize_entity(pagamento, usuario_id, projeto_repo)
    except NaoEncontradoException as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValidaEntidadeException, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
