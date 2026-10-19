"""Interactive helper: password is never part of a shell command/history."""
from getpass import getpass
from urllib.parse import quote

host = input('Session pooler host: ').strip()
user = input('Usuário (postgres.PROJECT_REF): ').strip()
password = getpass('Senha do banco: ')
print('\nDATABASE_URL (Render):')
print(f'postgresql+asyncpg://{quote(user, safe="")}:{quote(password, safe="")}@{host}:5432/postgres')
print('\nBACKUP_DATABASE_URL (GitHub Secret):')
print(f'postgresql://{quote(user, safe="")}:{quote(password, safe="")}@{host}:5432/postgres')
