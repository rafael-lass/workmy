"""Orquestração da leitura consistente e geração de planilhas em blocos."""
from time import perf_counter
from starlette.concurrency import run_in_threadpool
from src.application.dto.excel_export import ExportPeriod, ExportResult
from src.application.ports.outbound.i_excel_export import IExcelExportQuery, IExcelRenderer


class ExportarDashboardUseCase:
    def __init__(self, query: IExcelExportQuery, renderer: IExcelRenderer):
        self.query, self.renderer = query, renderer

    async def run(self, user_id: int, period: ExportPeriod, mode: str = 'parallel') -> ExportResult:
        if mode not in {'parallel', 'sequential'}:
            raise ValueError('Modo de exportação inválido.')
        started = perf_counter()
        timings, data = {}, {}
        async with self.query.snapshot():
            for name, task in [('pagamentos', self.query.payments), ('projetos', self.query.projects),
                               ('clientes', self.query.clients), ('servicos', self.query.services)]:
                begin = perf_counter()
                data[name] = await task(user_id, period)
                timings[f'consulta_{name}'] = perf_counter() - begin
        begin = perf_counter()
        path, workbook_timings, file_sizes = await run_in_threadpool(self.renderer.render, data, period, mode)
        timings.update(workbook_timings)
        timings['render_total'] = perf_counter() - begin
        timings['total'] = perf_counter() - started
        return ExportResult(path, f'workmy-relatorios-{period.key}-{period.today.isoformat()}.zip',
                            timings, {key: len(rows) for key, rows in data.items()}, file_sizes)
