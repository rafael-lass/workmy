from fastapi import APIRouter, Depends

from src.application.ports.outbound.i_dashboard_query import IDashboardQuery
from src.application.ports.outbound.i_pagamento_repository import IPagamentoRepository
from src.domain.time import business_today
from src.presentation.dependencies import get_dashboard_query, get_pagamento_repository
from src.presentation.dto.schemas import DashboardResumoOutSchema
from src.presentation.middleware.auth import get_current_user_id
from src.presentation.rest.pagamentos import pagamento_view_to_dict


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/resumo", response_model=DashboardResumoOutSchema)
async def get_dashboard_resumo(
    usuario_id: int = Depends(get_current_user_id),
    query: IDashboardQuery = Depends(get_dashboard_query),
    pagamento_repo: IPagamentoRepository = Depends(get_pagamento_repository),
):
    resumo = await query.get_resumo(usuario_id, business_today())
    recentes, _ = await pagamento_repo.list_with_names(
        usuario_id,
        {"status": "PAGO"},
        page=1,
        page_size=5,
    )
    return {
        **resumo,
        "ultimos_recebimentos": [pagamento_view_to_dict(item) for item in recentes],
    }
