"""Compara a exportação sequencial e paralela do ZIP; somente leitura no banco."""
import argparse
import asyncio
from datetime import date, datetime
from zoneinfo import ZoneInfo
import json
import os
from pathlib import Path
import platform
from statistics import median
import sys
import time
import hashlib
from io import BytesIO
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.application.dto.excel_export import ExportPeriod
from src.application.usecases.exportar_dashboard import ExportarDashboardUseCase
from src.domain.time import business_today
from src.infrastructure.documents.dashboard_excel import DashboardExcelRenderer
from src.infrastructure.persistence.models import UsuarioModel
from src.infrastructure.persistence.repositories.postgres_excel_query import PostgresExcelQuery


def content_signature(path):
    """Confere XML de todas as células/estilos, ignorando timestamps do contêiner ZIP."""
    hashes = {}
    with ZipFile(path) as package:
        for filename in sorted(package.namelist()):
            digest = hashlib.sha256()
            with ZipFile(BytesIO(package.read(filename))) as book:
                for part in ('xl/workbook.xml', 'xl/styles.xml', 'xl/worksheets/sheet1.xml'):
                    digest.update(part.encode())
                    with book.open(part) as stream:
                        while block := stream.read(1024 * 1024):
                            digest.update(block)
            hashes[filename] = digest.hexdigest()
    return hashes


async def benchmark(args):
    url = make_url(os.environ['DATABASE_URL'])
    if url.get_backend_name() != 'postgresql':
        raise ValueError('Benchmark exige PostgreSQL explicitamente configurado.')
    engine = create_async_engine(url.set(drivername='postgresql+asyncpg'), hide_parameters=True)
    sessions = async_sessionmaker(engine)
    runs = []
    try:
        async with sessions() as session:
            user_id = await session.scalar(select(UsuarioModel.id).where(UsuarioModel.username == args.username))
            if user_id is None:
                raise ValueError('Usuário não encontrado.')
        for period in args.periods:
            for repetition in range(args.repeats):
                modes = ['sequential', 'parallel'] if args.mode == 'compare' else [args.mode]
                if args.mode == 'compare' and repetition % 2:
                    modes.reverse()
                for mode in modes:
                    started = time.time()
                    started_at = datetime.fromtimestamp(started, ZoneInfo('America/Sao_Paulo')).isoformat(timespec='milliseconds')
                    print(f'INÍCIO {mode}: {started_at}', flush=True)
                    monotonic_started = time.perf_counter()
                    async with sessions() as session:
                        result = await ExportarDashboardUseCase(PostgresExcelQuery(session),
                            DashboardExcelRenderer(workers=args.workers, batch_size=args.batch_size)).run(
                            user_id, ExportPeriod.create(period, args.reference), mode=mode)
                    finished = time.time()
                    finished_at = datetime.fromtimestamp(finished, ZoneInfo('America/Sao_Paulo')).isoformat(timespec='milliseconds')
                    wall_seconds = finished - started
                    monotonic_seconds = time.perf_counter() - monotonic_started
                    print(f'FIM {mode}: {finished_at} | TEMPO: {wall_seconds:.3f} segundos', flush=True)
                    try:
                        runs.append({'mode': mode, 'period': period, 'repetition': repetition + 1,
                                     'started_at': started_at, 'finished_at': finished_at,
                                     'started_epoch': started, 'finished_epoch': finished,
                                     'wall_time_seconds': wall_seconds, 'timings_seconds': result.timings,
                                     'monotonic_seconds': monotonic_seconds,
                                     'counts': result.counts, 'file_sizes': result.file_sizes,
                                     'content_sha256': content_signature(result.path)})
                        print(f"CONFERÊNCIA: {result.counts}; conteúdo SHA-256 registrado.", flush=True)
                        args.output.parent.mkdir(parents=True, exist_ok=True)
                        args.output.write_text(json.dumps({'status': 'running', 'runs': runs}, indent=2), encoding='utf-8')
                        if abs(wall_seconds - monotonic_seconds) > max(1, monotonic_seconds * .1):
                            raise RuntimeError('Relógios divergentes: possível suspensão/ajuste do sistema. Repetir medição.')
                        reference = next(run for run in runs if run['period'] == period)
                        if reference['content_sha256'] != runs[-1]['content_sha256']:
                            raise RuntimeError('Conteúdo das células/estilos divergente entre execuções. Comparação inválida.')
                    finally:
                        result.path.unlink(missing_ok=True)
    finally:
        await engine.dispose()
    report = {'status': 'complete', 'implementation': 'multiprocessing_pool_row_blocks',
        'timezone': 'America/Sao_Paulo', 'mode': args.mode, 'reference': str(args.reference),
        'workers': args.workers, 'batch_size': args.batch_size, 'content_equal': True,
        'python': platform.python_version(), 'platform': platform.platform(), 'cpu_count': os.cpu_count(),
        'repeats': args.repeats, 'runs': runs,
        'results': {period: {mode: {
            'median_wall_time_seconds': median(r['wall_time_seconds'] for r in runs if r['period'] == period and r['mode'] == mode),
            'median_stages_seconds': {stage: median(r['timings_seconds'][stage] for r in runs if r['period'] == period and r['mode'] == mode)
                for stage in runs[0]['timings_seconds'] if all(stage in run['timings_seconds'] for run in runs if run['period'] == period and run['mode'] == mode)},
            'file_sizes': next(r['file_sizes'] for r in runs if r['period'] == period and r['mode'] == mode),
            'counts': next(r['counts'] for r in runs if r['period'] == period and r['mode'] == mode),
        } for mode in sorted({r['mode'] for r in runs if r['period'] == period})} for period in args.periods}}
    for period, modes in report['results'].items():
        if {'sequential', 'parallel'} <= modes.keys():
            seq = modes['sequential']['median_wall_time_seconds']
            par = modes['parallel']['median_wall_time_seconds']
            if modes['sequential']['counts'] != modes['parallel']['counts']:
                raise RuntimeError(f'Contagens divergentes entre modos no período {period}.')
            modes['parallel_speedup'] = seq / par if par else None
            modes['parallel_time_saved_seconds'] = seq - par
            modes['parallel_reduction_percent'] = 100 * (1 - par / seq) if seq else None
            print(f'RESULTADO {period}: sequencial={seq:.3f}s | paralelo={par:.3f}s | '
                  f'ganho={seq/par:.3f}x | economia={seq-par:.3f}s', flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--username', required=True)
    parser.add_argument('--periods', nargs='+', choices=['3', '6', '12', 'total'], default=['3', '6', '12', 'total'])
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--mode', choices=['sequential', 'parallel', 'compare'], default='compare')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--batch-size', type=int, default=25000)
    parser.add_argument('--reference', type=date.fromisoformat, default=business_today())
    parser.add_argument('--output', type=Path, default=Path('benchmark-excel-comparacao.json'))
    args = parser.parse_args()
    if min(args.repeats, args.workers, args.batch_size) < 1:
        parser.error('--repeats, --workers e --batch-size devem ser positivos')
    asyncio.run(benchmark(args))
