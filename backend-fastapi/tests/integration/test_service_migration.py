import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys


def test_migration_preserves_legacy_services_and_deduplicates_tags(tmp_path):
    database = tmp_path / 'migration.sqlite3'
    root = Path(__file__).resolve().parents[2]
    env = {**os.environ, 'DATABASE_URL': f'sqlite+aiosqlite:///{database.as_posix()}'}
    def migrate(revision):
        subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', revision], cwd=root, env=env, check=True, capture_output=True)
    migrate('20260905_0001')
    with sqlite3.connect(database) as connection:
        connection.execute("INSERT INTO usuarios (id, username, email, password_hash) VALUES (1, 'legacy', 'legacy@example.com', 'hash')")
        for identifier, tags in [(1, 'Web, web,  Design '), (2, 'DESIGN')]:
            connection.execute("INSERT INTO servicos (id, usuario_id, nome, descricao, tags, ferramentas, github_repo, imagem_bytes, imagem_mime, criado_em) VALUES (?, 1, ?, ?, ?, 'Python', 'https://example.com', ?, 'image/png', CURRENT_TIMESTAMP)", (identifier, f'Serviço {identifier}', 'Olá\nSegunda linha', tags, b'original-image'))
    migrate('head')
    with sqlite3.connect(database) as connection:
        rows = connection.execute('SELECT descricao, descricao_documento, ferramentas, github_repo, imagem_bytes FROM servicos').fetchall()
        assert len(rows) == 2
        for row in rows:
            assert row[0] == 'Olá\nSegunda linha'
            assert json.loads(row[1])['doc']['content'][1]['content'][0]['text'] == 'Segunda linha'
            assert row[2:] == ('Python', 'https://example.com', b'original-image')
        assert connection.execute('SELECT count(*) FROM tags').fetchone()[0] == 2
        assert connection.execute('SELECT count(*) FROM servico_tags').fetchone()[0] == 3
    subprocess.run([sys.executable, '-m', 'alembic', 'check'], cwd=root, env=env, check=True, capture_output=True)
