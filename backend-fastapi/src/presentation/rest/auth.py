from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from src.presentation.dto.schemas import (
    UserLoginSchema,
    UserRegisterSchema,
    ErrorSchema,
    MessageSchema,
    AuthResponseSchema,
    RefreshTokenInSchema,
    AccessTokenOutSchema,
    UserProfileSchema,
)
from src.application.usecases.auth_usecases import AuthUseCases
from src.presentation.dependencies import get_auth_usecases, get_token_service, get_usuario_repository
from src.application.ports.outbound.i_usuario_repository import IUsuarioRepository
from src.application.ports.outbound.i_token_service import ITokenService
from src.domain.exceptions.business_exceptions import ValidaEntidadeException, NaoEncontradoException
from src.presentation.middleware.auth import (
    get_current_user_id,
    revoke_token,
    security as bearer_security,
)

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.get("/me", response_model=UserProfileSchema)
async def me(
    usuario_id: int = Depends(get_current_user_id),
    usuario_repo: IUsuarioRepository = Depends(get_usuario_repository),
):
    usuario = await usuario_repo.get_by_id(usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return {
        "id": usuario.id,
        "username": usuario.username,
        "email": usuario.email,
        "telefone": usuario.telefone,
    }

@router.post("/register", response_model=AuthResponseSchema, responses={400: {"model": ErrorSchema}})
async def register(
    payload: UserRegisterSchema,
    auth_usecases: AuthUseCases = Depends(get_auth_usecases)
):
    """Registra um novo usuário no sistema de forma segura."""
    try:
        usuario, access, refresh = await auth_usecases.registrar(
            username=payload.username,
            email=payload.email,
            password_raw=payload.password,
            telefone=payload.telefone
        )
        return {
            "access": access,
            "refresh": refresh,
            "user": {
                "id": usuario.id,
                "username": usuario.username,
                "email": usuario.email,
                "telefone": usuario.telefone
            }
        }
    except ValidaEntidadeException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=AuthResponseSchema, responses={401: {"model": ErrorSchema}})
async def login(
    payload: UserLoginSchema,
    auth_usecases: AuthUseCases = Depends(get_auth_usecases)
):
    """Autentica o usuário e emite os tokens JWT correspondentes."""
    try:
        usuario, access, refresh = await auth_usecases.login(
            email_ou_username=payload.email,
            password_raw=payload.password
        )
        return {
            "access": access,
            "refresh": refresh,
            "user": {
                "id": usuario.id,
                "username": usuario.username,
                "email": usuario.email,
                "telefone": usuario.telefone
            }
        }
    except NaoEncontradoException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except ValidaEntidadeException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.post("/refresh", response_model=AccessTokenOutSchema, responses={401: {"model": ErrorSchema}})
async def refresh_token(
    payload: RefreshTokenInSchema,
    auth_usecases: AuthUseCases = Depends(get_auth_usecases)
):
    """Renova o access token usando o refresh token. Busca dados reais do usuário no banco."""
    try:
        access = await auth_usecases.refresh(payload.refresh)
        return {"access": access}
    except (ValidaEntidadeException, NaoEncontradoException) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.post("/logout", response_model=MessageSchema)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_security),
    token_service: ITokenService = Depends(get_token_service),
):
    """
    Desloga o usuário invalidando o access token atual via JTI blacklist.
    O BFF é responsável por limpar os cookies HTTP-Only no cliente.
    """
    token = credentials.credentials
    payload = token_service.decode_token(token)

    if payload:
        jti = payload.get("jti")
        if jti:
            revoke_token(jti)

    return {"message": "Deslogado com sucesso. Token revogado."}

