"""Validated cloud settings shared by the API and Alembic."""
import os
import ssl
from urllib.parse import urlsplit

from sqlalchemy.engine import make_url


def is_cloud() -> bool:
    return os.getenv('APP_ENV') == 'cloud'


def database_url() -> str:
    value = os.getenv('DATABASE_URL', '')
    if is_cloud():
        if not value or make_url(value).drivername != 'postgresql+asyncpg':
            raise ValueError('Cloud exige DATABASE_URL PostgreSQL com driver asyncpg.')
        secret = os.getenv('JWT_SECRET_KEY', '')
        if len(secret) < 32 or secret in {'dev_secret_change_me_in_production', 'generate_a_long_random_secret'}:
            raise ValueError('Cloud exige JWT_SECRET_KEY permanente com pelo menos 32 caracteres.')
        origin = os.getenv('APP_PUBLIC_URL', '')
        parsed = urlsplit(origin)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username:
            raise ValueError('APP_PUBLIC_URL deve ser uma origem HTTPS, sem barra final.')
        if os.getenv('CORS_ORIGINS') != origin:
            raise ValueError('CORS_ORIGINS deve ser igual a APP_PUBLIC_URL no cloud.')
    return value or 'sqlite+aiosqlite:///./db.sqlite3'


def connection_args(url: str) -> dict:
    if url.startswith('sqlite'):
        return {'check_same_thread': False}
    if is_cloud():
        # asyncpg receives SSLContext, not libpq's sslmode query parameter.
        ca = os.getenv('DATABASE_CA_CERT', '')
        if not ca:
            raise ValueError('Cloud exige DATABASE_CA_CERT em formato PEM.')
        context = ssl.create_default_context(cadata=ca)
        return {'ssl': context, 'timeout': 10}
    return {}


def engine_options(url: str) -> dict:
    options = {'connect_args': connection_args(url), 'pool_pre_ping': True}
    if url.startswith('postgresql'):
        options.update(pool_size=2, max_overflow=1, pool_timeout=10)
    return options
