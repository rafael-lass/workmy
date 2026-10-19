from fastapi import APIRouter, Depends, HTTPException
import os
from threading import BoundedSemaphore
from typing import Literal
import logging
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.persistence.session import get_db_session
from src.infrastructure.persistence.repositories.postgres_excel_query import PostgresExcelQuery
from src.infrastructure.documents.dashboard_excel import DashboardExcelRenderer
from src.application.usecases.exportar_dashboard import ExportarDashboardUseCase, ExportBusy, ExportLimitExceeded
from src.application.dto.excel_export import ExportPeriod

from src.application.ports.outbound.i_dashboard_query import IDashboardQuery
from src.application.ports.outbound.i_pagamento_repository import IPagamentoRepository
from src.domain.time import business_today
from src.presentation.dependencies import get_dashboard_query, get_pagamento_repository
from src.presentation.dto.schemas import DashboardResumoOutSchema
from src.presentation.middleware.auth import get_current_user_id
from src.presentation.rest.pagamentos import pagamento_view_to_dict


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
_cloud = os.getenv('APP_ENV') == 'cloud'
EXPORT_MODE = os.getenv('EXCEL_EXPORT_MODE', 'sequential' if _cloud else 'parallel')
EXPORT_MAX_ROWS = int(os.getenv('EXCEL_EXPORT_MAX_ROWS', '2000' if _cloud else '0'))
_capacity = int(os.getenv('EXCEL_EXPORT_MAX_CONCURRENT', '1' if _cloud else '0'))
if EXPORT_MODE not in {'parallel', 'sequential'} or EXPORT_MAX_ROWS < 0 or _capacity < 0:
    raise ValueError('Configuração de exportação inválida.')
if _cloud and (EXPORT_MODE != 'sequential' or not 1 <= EXPORT_MAX_ROWS <= 2000 or _capacity != 1):
    raise ValueError('Cloud gratuito exige modo sequencial, até 2000 registros e concorrência 1.')
EXPORT_GATE = BoundedSemaphore(_capacity) if _capacity else None


@router.get('/exportar.zip')
async def export_dashboard(
    periodo: Literal['3', '6', '12', 'total'] = '3',
    usuario_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        result = await ExportarDashboardUseCase(PostgresExcelQuery(session), DashboardExcelRenderer()).run(
            usuario_id, ExportPeriod.create(periodo, business_today()), EXPORT_MODE,
            max_rows=EXPORT_MAX_ROWS, gate=EXPORT_GATE)
    except ExportLimitExceeded as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ExportBusy as exc:
        raise HTTPException(status_code=429, detail=str(exc), headers={'Retry-After': '5'}) from exc
    logging.getLogger(__name__).info('Exportação %s: contagens=%s arquivos=%s tempos=%s', EXPORT_MODE,
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
