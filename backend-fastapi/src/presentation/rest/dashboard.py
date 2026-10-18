from fastapi import APIRouter, Depends
from typing import Literal
import logging
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.persistence.session import get_db_session
from src.infrastructure.persistence.repositories.postgres_excel_query import PostgresExcelQuery
from src.infrastructure.documents.dashboard_excel import DashboardExcelRenderer
from src.application.usecases.exportar_dashboard import ExportarDashboardUseCase
from src.application.dto.excel_export import ExportPeriod

from src.application.ports.outbound.i_dashboard_query import IDashboardQuery
from src.application.ports.outbound.i_pagamento_repository import IPagamentoRepository
from src.domain.time import business_today
from src.presentation.dependencies import get_dashboard_query, get_pagamento_repository
from src.presentation.dto.schemas import DashboardResumoOutSchema
from src.presentation.middleware.auth import get_current_user_id
from src.presentation.rest.pagamentos import pagamento_view_to_dict


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get('/exportar.zip')
async def export_dashboard(
    periodo: Literal['3', '6', '12', 'total'] = '3',
    usuario_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    result = await ExportarDashboardUseCase(PostgresExcelQuery(session), DashboardExcelRenderer()).run(
        usuario_id, ExportPeriod.create(periodo, business_today()))
    logging.getLogger(__name__).info('Exportação %s: contagens=%s arquivos=%s tempos=%s', 'paralela',
        result.counts, result.file_sizes, result.timings)
    return FileResponse(result.path, filename=result.filename,
        media_type='application/zip',
        headers={'Cache-Control': 'no-store'},
        background=BackgroundTask(result.path.unlink, missing_ok=True))


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
