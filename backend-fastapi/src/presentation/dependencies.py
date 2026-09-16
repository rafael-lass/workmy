from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.session import get_db_session

# Repositories
from src.infrastructure.persistence.repositories.postgres_usuario_repo import PostgresUsuarioRepository
from src.infrastructure.persistence.repositories.postgres_cliente_repo import PostgresClienteRepository
from src.infrastructure.persistence.repositories.postgres_servico_repo import PostgresServicoRepository
from src.infrastructure.persistence.repositories.postgres_projeto_repo import PostgresProjetoRepository
from src.infrastructure.persistence.repositories.postgres_pagamento_repo import PostgresPagamentoRepository
from src.infrastructure.persistence.repositories.postgres_dashboard_query import PostgresDashboardQuery

# Adapters
from src.infrastructure.security.adapters import BcryptPasswordHasher, JwtTokenService

# Use Cases
from src.application.usecases.auth_usecases import AuthUseCases
from src.application.usecases.crud_cliente import CrudClienteUseCase
from src.application.usecases.crud_servico import CrudServicoUseCase
from src.application.usecases.criar_projeto import CriarProjetoUseCase
from src.application.usecases.atualizar_projeto import AtualizarProjetoUseCase
from src.application.usecases.deletar_projeto import DeletarProjetoUseCase
from src.application.usecases.crud_pagamento import CrudPagamentoUseCase
from src.application.usecases.faturar_recorrencias import FaturarRecorrenciasUseCase
from src.application.ports.outbound.i_cliente_repository import IClienteRepository
from src.application.ports.outbound.i_dashboard_query import IDashboardQuery
from src.application.ports.outbound.i_pagamento_repository import IPagamentoRepository
from src.application.ports.outbound.i_projeto_repository import IProjetoRepository
from src.application.ports.outbound.i_servico_repository import IServicoRepository
from src.application.ports.outbound.i_usuario_repository import IUsuarioRepository
from src.application.ports.outbound.i_token_service import ITokenService


def get_usuario_repository(session: AsyncSession = Depends(get_db_session)) -> IUsuarioRepository:
    return PostgresUsuarioRepository(session)


def get_cliente_repository(session: AsyncSession = Depends(get_db_session)) -> IClienteRepository:
    return PostgresClienteRepository(session)


def get_servico_repository(session: AsyncSession = Depends(get_db_session)) -> IServicoRepository:
    return PostgresServicoRepository(session)


def get_projeto_repository(session: AsyncSession = Depends(get_db_session)) -> IProjetoRepository:
    return PostgresProjetoRepository(session)


def get_pagamento_repository(session: AsyncSession = Depends(get_db_session)) -> IPagamentoRepository:
    return PostgresPagamentoRepository(session)


def get_dashboard_query(session: AsyncSession = Depends(get_db_session)) -> IDashboardQuery:
    return PostgresDashboardQuery(session)


def get_token_service() -> ITokenService:
    return JwtTokenService()

def get_auth_usecases(session: AsyncSession = Depends(get_db_session)) -> AuthUseCases:
    return AuthUseCases(
        usuario_repo=PostgresUsuarioRepository(session),
        password_hasher=BcryptPasswordHasher(),
        token_service=JwtTokenService()
    )

def get_crud_cliente_usecase(session: AsyncSession = Depends(get_db_session)) -> CrudClienteUseCase:
    return CrudClienteUseCase(
        cliente_repo=PostgresClienteRepository(session)
    )

def get_crud_servico_usecase(session: AsyncSession = Depends(get_db_session)) -> CrudServicoUseCase:
    return CrudServicoUseCase(
        servico_repo=PostgresServicoRepository(session)
    )

def get_criar_projeto_usecase(session: AsyncSession = Depends(get_db_session)) -> CriarProjetoUseCase:
    return CriarProjetoUseCase(
        projeto_repo=PostgresProjetoRepository(session),
        cliente_repo=PostgresClienteRepository(session),
        servico_repo=PostgresServicoRepository(session)
    )

def get_atualizar_projeto_usecase(session: AsyncSession = Depends(get_db_session)) -> AtualizarProjetoUseCase:
    return AtualizarProjetoUseCase(
        projeto_repo=PostgresProjetoRepository(session)
    )

def get_deletar_projeto_usecase(session: AsyncSession = Depends(get_db_session)) -> DeletarProjetoUseCase:
    return DeletarProjetoUseCase(
        projeto_repo=PostgresProjetoRepository(session)
    )

def get_crud_pagamento_usecase(session: AsyncSession = Depends(get_db_session)) -> CrudPagamentoUseCase:
    return CrudPagamentoUseCase(
        pagamento_repo=PostgresPagamentoRepository(session),
        projeto_repo=PostgresProjetoRepository(session)
    )

def get_faturar_recorrencias_usecase(session: AsyncSession = Depends(get_db_session)) -> FaturarRecorrenciasUseCase:
    return FaturarRecorrenciasUseCase(
        projeto_repo=PostgresProjetoRepository(session),
        pagamento_repo=PostgresPagamentoRepository(session)
    )
