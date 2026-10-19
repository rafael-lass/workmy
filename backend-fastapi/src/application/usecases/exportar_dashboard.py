"""Orquestração da leitura consistente e geração de planilhas em blocos."""
from time import perf_counter
import asyncio
from starlette.concurrency import run_in_threadpool
from src.application.dto.excel_export import ExportPeriod, ExportResult
from src.application.ports.outbound.i_excel_export import IExcelExportQuery, IExcelRenderer


class ExportLimitExceeded(Exception):
    pass


class ExportBusy(Exception):
    pass


# Keep detached renders alive until their thread finishes, including on disconnect.
_renders: set[asyncio.Task] = set()


class ExportarDashboardUseCase:
    def __init__(self, query: IExcelExportQuery, renderer: IExcelRenderer):
        self.query, self.renderer = query, renderer

    async def run(self, user_id: int, period: ExportPeriod, mode: str = 'parallel', *, max_rows: int = 0, gate=None) -> ExportResult:
        if mode not in {'parallel', 'sequential'}:
            raise ValueError('Modo de exportação inválido.')
        started = perf_counter()
        timings, data = {}, {}
        if gate is not None and not gate.acquire(blocking=False):
            raise ExportBusy('Outra exportação está em andamento. Tente novamente em instantes.')
        rendering = False
        try:
            async with self.query.snapshot():
                if max_rows and await self.query.count_rows(user_id, period) > max_rows:
                    raise ExportLimitExceeded(f'A demonstração permite até {max_rows} registros por exportação. Reduza o período.')
                for name, task in [('pagamentos', self.query.payments), ('projetos', self.query.projects),
                                   ('clientes', self.query.clients), ('servicos', self.query.services)]:
                    begin = perf_counter()
                    data[name] = await task(user_id, period)
                    timings[f'consulta_{name}'] = perf_counter() - begin
            begin = perf_counter()

            def render():
                try:
                    return self.renderer.render(data, period, mode)
                finally:
                    if gate is not None:
                        gate.release()

            task = asyncio.create_task(run_in_threadpool(render))
            rendering = True
            _renders.add(task)
            task.add_done_callback(_renders.discard)
            try:
                path, workbook_timings, file_sizes = await asyncio.shield(task)
            except asyncio.CancelledError:
                def cleanup(completed):
                    try:
                        completed.result()[0].unlink(missing_ok=True)
                    except BaseException:
                        pass
                task.add_done_callback(cleanup)
                raise
        finally:
            if gate is not None and not rendering:
                gate.release()
        timings.update(workbook_timings)
        timings['render_total'] = perf_counter() - begin
        timings['total'] = perf_counter() - started
        return ExportResult(path, f'workmy-relatorios-{period.key}-{period.today.isoformat()}.zip',
                            timings, {key: len(rows) for key, rows in data.items()}, file_sizes)
