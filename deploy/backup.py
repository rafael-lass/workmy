"""Cloud backup: database credentials only in env; only encrypted files survive."""
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit, unquote
import os
import subprocess


def backup():
    url = urlsplit(os.environ['BACKUP_DATABASE_URL'])
    if url.scheme not in {'postgres', 'postgresql'} or not url.hostname or not url.username or not url.password:
        raise ValueError('BACKUP_DATABASE_URL deve ser uma conexão PostgreSQL completa.')
    ca = os.environ['DATABASE_CA_CERT']
    passphrase = os.environ['BACKUP_PASSPHRASE']
    if len(passphrase) < 32:
        raise ValueError('BACKUP_PASSPHRASE exige pelo menos 32 caracteres.')
    output = Path(os.getenv('BACKUP_OUTPUT_DIR', 'backup-artifacts')).resolve()
    output.mkdir(exist_ok=True)
    destination = output / f'workmy-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.dump.gpg'
    env = os.environ.copy()
    env.update(PGHOST=url.hostname, PGPORT=str(url.port or 5432), PGUSER=unquote(url.username),
               PGPASSWORD=unquote(url.password), PGDATABASE=unquote(url.path.lstrip('/')),
               PGSSLMODE='verify-full', PGSSLROOTCERT='/backup/ca.crt')
    with TemporaryDirectory(prefix='workmy-backup-') as temporary:
        folder = Path(temporary)
        (folder / 'ca.crt').write_text(ca, encoding='utf-8')
        docker = ['docker', 'run', '--rm']
        if env.get('BACKUP_DOCKER_NETWORK'):
            docker += ['--network', env['BACKUP_DOCKER_NETWORK']]
        docker += ['-v', f'{folder}:/backup']
        for key in ['PGHOST', 'PGPORT', 'PGUSER', 'PGPASSWORD', 'PGDATABASE', 'PGSSLMODE', 'PGSSLROOTCERT']:
            docker += ['--env', key]

        def run(command):
            result = subprocess.run(command, env=env, capture_output=True)
            if result.returncode:
                raise RuntimeError('Backup falhou. Confira conexão, CA e disponibilidade do banco. Credenciais e stderr do driver foram omitidos.')
            return result.stdout.decode().strip()

        version = run(docker + ['postgres:17-bookworm', 'psql', '-Atc', 'SHOW server_version_num'])
        major = int(version) // 10000
        if not 14 <= major <= 20:
            raise ValueError('Versão PostgreSQL não suportada pelo roteiro.')
        run(docker + [f'postgres:{major}-bookworm', 'pg_dump', '-Fc', '-n', 'public',
                      '--no-owner', '--no-acl', '-f', '/backup/workmy.dump'])
        subprocess.run(['gpg', '--batch', '--yes', '--pinentry-mode', 'loopback', '--passphrase-fd', '0',
                        '--symmetric', '--cipher-algo', 'AES256', '--output', str(destination), str(folder / 'workmy.dump')],
                       input=(passphrase + '\n').encode(), check=True, capture_output=True)
    print(f'Backup criptografado: {destination.name}')
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as stream:
            stream.write(f'backup_file={destination}\n')
    return destination


if __name__ == '__main__':
    try:
        backup()
    except Exception as exc:
        # Avoid a traceback containing connection options or subprocess details.
        print(f'Backup não concluído ({type(exc).__name__}). Consulte o guia DEPLOY_CLOUD.md.')
        raise SystemExit(1)
