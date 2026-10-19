from src.infrastructure.config import database_url, engine_options
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# URL padrão para SQLite assíncrono caso nenhuma variável esteja configurada
DATABASE_URL = database_url()

# Configura a Engine do SQLAlchemy assíncrona
# Desativa pooling de threads para SQLite simples para evitar colisões de threads de testes

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    **engine_options(DATABASE_URL)
)

# Fabrica sessões assíncronas do banco
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Classe Base declarativa para os modelos físicos do ORM
class Base(DeclarativeBase):
    pass

# Dependency local para rotas do FastAPI obterem sessão do banco
async def get_db_session():
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
