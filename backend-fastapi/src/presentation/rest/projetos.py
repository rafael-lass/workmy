from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from src.presentation.dto.schemas import (
    ProjetoInSchema,
    ProjetoUpdateSchema,
    ProjetoOutSchema,
    ErrorSchema,
    MessageSchema,
    RecorrenciaInSchema,
    RecorrenciaOutSchema,
    UpdateStatusSchema
)
from src.presentation.middleware.auth import get_current_user_id

from src.application.usecases.criar_projeto import CriarProjetoUseCase
from src.application.usecases.atualizar_projeto import AtualizarProjetoUseCase
from src.application.usecases.deletar_projeto import DeletarProjetoUseCase
from src.application.usecases.faturar_recorrencias import FaturarRecorrenciasUseCase
from src.domain.time import business_today
from src.application.ports.outbound.i_projeto_repository import IProjetoRepository

from src.presentation.dependencies import (
    get_criar_projeto_usecase,
    get_atualizar_projeto_usecase,
    get_deletar_projeto_usecase,
    get_projeto_repository,
    get_faturar_recorrencias_usecase,
)
from src.domain.exceptions.business_exceptions import (
    ColisaoContratoException,
    ConflitoDeletarException,
    NaoEncontradoException,
    ValidaEntidadeException,
)

router = APIRouter(prefix="/projetos", tags=["Projetos"])

def _view_to_dict(view) -> dict:
    return {
        "id": view.id,
        "cliente_id": view.cliente_id,
        "cliente_nome": view.cliente_nome,
        "servico_id": view.servico_id,
        "servico_nome": view.servico_nome,
        "valor": str(view.valor) if view.valor else None,
        "valor_mensal": str(view.valor_mensal) if view.valor_mensal else None,
        "dia_vencimento": view.dia_vencimento,
        "recorrencia_inicio": view.recorrencia_inicio.isoformat() if view.recorrencia_inicio else None,
        "criado_em": view.criado_em.isoformat() if view.criado_em else "",
        "status": view.status,
        "total_acumulado": str(view.total_acumulado),
        "possui_lancamentos": view.possui_lancamentos,
        "tipo_recorrencia": view.tipo_recorrencia,
        "ativo": view.recorrencia_ativa,
    }

@router.post(
    "/",
    response_model=ProjetoOutSchema,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorSchema}, 404: {"model": ErrorSchema}}
)
async def create_projeto(
    payload: ProjetoInSchema,
    usuario_id: int = Depends(get_current_user_id),
    use_case: CriarProjetoUseCase = Depends(get_criar_projeto_usecase),
    repo: IProjetoRepository = Depends(get_projeto_repository)
):
    try:
        projeto_criado = await use_case.execute(
            usuario_id=usuario_id,
            cliente_id=payload.cliente_id,
            servico_id=payload.servico_id,
            valor=payload.valor,
            tipo_recorrencia=payload.tipo_recorrencia,
            recorrencia_ativa=payload.ativo,
            valor_mensal=payload.valor_mensal,
            dia_vencimento=payload.dia_vencimento,
            recorrencia_inicio=payload.recorrencia_inicio,
        )
    except (ColisaoContratoException, ValidaEntidadeException, NaoEncontradoException) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    view = await repo.get_with_names(projeto_criado.id, usuario_id)
    if view:
        return _view_to_dict(view)

    raise HTTPException(status_code=500, detail="Erro ao buscar projeto recém criado.")

@router.put(
    "/{projeto_id}",
    response_model=ProjetoOutSchema,
    responses={400: {"model": ErrorSchema}, 404: {"model": ErrorSchema}}
)
async def update_projeto(
    projeto_id: int,
    payload: ProjetoUpdateSchema,
    usuario_id: int = Depends(get_current_user_id),
    use_case: AtualizarProjetoUseCase = Depends(get_atualizar_projeto_usecase),
    repo: IProjetoRepository = Depends(get_projeto_repository)
):
    try:
        changes = payload.model_dump(exclude_unset=True)
        if "ativo" in changes:
            changes["recorrencia_ativa"] = changes.pop("ativo")
        await use_case.execute(projeto_id, usuario_id, changes)
    except NaoEncontradoException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValidaEntidadeException as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    view = await repo.get_with_names(projeto_id, usuario_id)
    return _view_to_dict(view)

@router.get("/", response_model=List[ProjetoOutSchema])
async def list_projetos(
    cliente_id: int | None = None,
    usuario_id: int = Depends(get_current_user_id),
    repo: IProjetoRepository = Depends(get_projeto_repository)
):
    views = await repo.list_with_names(usuario_id, cliente_id)
    return [_view_to_dict(v) for v in views]

@router.get("/{projeto_id}", response_model=ProjetoOutSchema, responses={404: {"model": ErrorSchema}})
async def get_projeto(
    projeto_id: int,
    usuario_id: int = Depends(get_current_user_id),
    repo: IProjetoRepository = Depends(get_projeto_repository)
):
    view = await repo.get_with_names(projeto_id, usuario_id)
    if not view:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado.")
    return _view_to_dict(view)

@router.delete("/{projeto_id}", response_model=MessageSchema, responses={404: {"model": ErrorSchema}})
async def delete_projeto(
    projeto_id: int,
    usuario_id: int = Depends(get_current_user_id),
    use_case: DeletarProjetoUseCase = Depends(get_deletar_projeto_usecase)
):
    try:
        await use_case.execute(projeto_id, usuario_id)
        return {"message": "Projeto deletado com sucesso."}
    except NaoEncontradoException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ConflitoDeletarException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

@router.patch(
    "/{projeto_id}/recorrencia",
    response_model=RecorrenciaOutSchema,
    responses={400: {"model": ErrorSchema}, 404: {"model": ErrorSchema}}
)
async def configurar_recorrencia(
    projeto_id: int,
    payload: RecorrenciaInSchema,
    usuario_id: int = Depends(get_current_user_id),
    use_case: AtualizarProjetoUseCase = Depends(get_atualizar_projeto_usecase),
    repo: IProjetoRepository = Depends(get_projeto_repository),
    faturamento: FaturarRecorrenciasUseCase = Depends(get_faturar_recorrencias_usecase),
):
    projeto = await repo.get_by_id(projeto_id, usuario_id)
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")

    try:
        changes = payload.model_dump(exclude_unset=True)
        changes["recorrencia_ativa"] = changes.pop("ativo")
        if payload.ativo:
            changes["tipo_recorrencia"] = "MENSAL"
        projeto = await use_case.execute(projeto_id, usuario_id, changes)
        if payload.ativo:
            await faturamento.execute_projeto(projeto, business_today())
    except ValidaEntidadeException as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "ativo": projeto.recorrencia_ativa,
        "tipo_recorrencia": projeto.tipo_recorrencia,
        "valor_mensal": str(projeto.valor_mensal) if projeto.valor_mensal else None,
        "dia_vencimento": projeto.dia_vencimento,
        "recorrencia_inicio": projeto.recorrencia_inicio.isoformat() if projeto.recorrencia_inicio else None,
    }


@router.patch(
    "/{projeto_id}/status",
    response_model=ProjetoOutSchema,
    responses={400: {"model": ErrorSchema}, 404: {"model": ErrorSchema}}
)
async def update_projeto_status(
    projeto_id: int,
    payload: UpdateStatusSchema,
    usuario_id: int = Depends(get_current_user_id),
    use_case: AtualizarProjetoUseCase = Depends(get_atualizar_projeto_usecase),
    repo: IProjetoRepository = Depends(get_projeto_repository)
):
    try:
        projeto = await use_case.execute(
            projeto_id,
            usuario_id,
            {"status": payload.status},
        )
    except NaoEncontradoException as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValidaEntidadeException as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    view = await repo.get_with_names(projeto.id, usuario_id)
    return _view_to_dict(view)
