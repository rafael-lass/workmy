import asyncio
from contextlib import asynccontextmanager
from datetime import date
from threading import BoundedSemaphore, Event
from unittest.mock import AsyncMock

import httpx
import pytest

from src.application.dto.excel_export import ExportPeriod
from src.application.usecases.exportar_dashboard import ExportarDashboardUseCase, ExportLimitExceeded, ExportBusy
from src.infrastructure.config import database_url, connection_args
from src.presentation import main


class Query:
    def __init__(self, count=0):
        self.count = count
        self.payments = AsyncMock(return_value=[])
        self.projects = AsyncMock(return_value=[])
        self.clients = AsyncMock(return_value=[])
        self.services = AsyncMock(return_value=[])

    @asynccontextmanager
    async def snapshot(self):
        yield

    async def count_rows(self, *_):
        return self.count


async def test_limit_is_checked_before_reading_data_and_releases_admission():
    query, gate = Query(2001), BoundedSemaphore(1)
    with pytest.raises(ExportLimitExceeded):
        await ExportarDashboardUseCase(query, None).run(1, ExportPeriod.create('total', date.today()), max_rows=2000, gate=gate)
    query.payments.assert_not_called()
    assert gate.acquire(blocking=False)


async def test_disconnect_does_not_release_running_export_and_cleans_file(tmp_path):
    started, finish = Event(), Event()
    path = tmp_path / 'result.zip'
    gate = BoundedSemaphore(1)

    class Renderer:
        def render(self, *_):
            started.set()
            assert finish.wait(5)
            path.write_bytes(b'zip')
            return path, {}, {}

    usecase = ExportarDashboardUseCase(Query(), Renderer())
    period = ExportPeriod.create('total', date.today())
    task = asyncio.create_task(usecase.run(1, period, gate=gate))
    try:
        assert await asyncio.to_thread(started.wait, 5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        with pytest.raises(ExportBusy):
            await usecase.run(1, period, gate=gate)
    finally:
        finish.set()
    for _ in range(100):
        await asyncio.sleep(.01)
        if gate.acquire(blocking=False):
            break
    else:
        pytest.fail('Render slot was not released')
    await asyncio.sleep(.05)
    assert not path.exists()


async def test_failed_renderer_releases_admission():
    class Broken:
        def render(self, *_):
            raise RuntimeError('render failed')
    gate = BoundedSemaphore(1)
    with pytest.raises(RuntimeError):
        await ExportarDashboardUseCase(Query(), Broken()).run(1, ExportPeriod.create('total', date.today()), gate=gate)
    assert gate.acquire(blocking=False)


async def test_readiness_queries_database_and_sanitizes_failure(monkeypatch):
    connection = AsyncMock()
    class Engine:
        @asynccontextmanager
        async def connect(self):
            yield connection
    monkeypatch.setattr(main, 'engine', Engine())
    monkeypatch.setenv('APP_COMMIT_SHA', 'tested-sha')
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url='http://test') as client:
        response = await client.get('/api/health/ready')
        assert response.json() == {'status': 'ready', 'commit': 'tested-sha'}
        connection.execute.assert_awaited_once()
        connection.execute.side_effect = RuntimeError('secret-database-password')
        response = await client.get('/api/health/ready')
        assert response.status_code == 503
        assert 'secret' not in response.text
        assert response.headers['cache-control'] == 'no-store'


def test_cloud_rejects_fallback_database_and_missing_tls(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'cloud')
    monkeypatch.delenv('DATABASE_URL', raising=False)
    with pytest.raises(ValueError, match='PostgreSQL'):
        database_url()
    monkeypatch.setenv('DATABASE_URL', 'postgresql+asyncpg://user:pass@host:5432/postgres')
    monkeypatch.setenv('JWT_SECRET_KEY', 'short')
    with pytest.raises(ValueError, match='JWT_SECRET_KEY'):
        database_url()
    monkeypatch.setenv('JWT_SECRET_KEY', 'a' * 48)
    monkeypatch.setenv('APP_PUBLIC_URL', 'https://workmy.vercel.app')
    monkeypatch.setenv('CORS_ORIGINS', '*')
    with pytest.raises(ValueError, match='CORS_ORIGINS'):
        database_url()
    monkeypatch.setenv('CORS_ORIGINS', 'https://workmy.vercel.app')
    assert database_url().startswith('postgresql+asyncpg')
    monkeypatch.delenv('DATABASE_CA_CERT', raising=False)
    with pytest.raises(ValueError, match='DATABASE_CA_CERT'):
        connection_args(database_url())
