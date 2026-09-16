from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.application.ports.outbound.i_token_service import ITokenService
from src.presentation.dependencies import get_token_service

# ---------------------------------------------------------------------------
# Token Blacklist em memória.
# Guarda os 'jti' (JWT IDs) de tokens revogados via logout.
# Em produção multi-instância, substituir por Redis compartilhado.
# ---------------------------------------------------------------------------
_token_blacklist: set[str] = set()


def revoke_token(jti: str) -> None:
    """Adiciona um JTI à blacklist (tokens inválidos após logout)."""
    _token_blacklist.add(jti)


def is_token_revoked(jti: str) -> bool:
    """Verifica se um JTI está na blacklist."""
    return jti in _token_blacklist


# Define o esquema de recebimento do Bearer Token HTTP
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_service: ITokenService = Depends(get_token_service),
) -> int:
    """
    Middleware/Dependency do FastAPI que extrai, decodifica e valida o JWT
    recebido no cabeçalho 'Authorization: Bearer <token>'.
    Verifica tipo de token, JTI na blacklist e retorna o ID do usuário autenticado.
    """
    token = credentials.credentials
    payload = token_service.decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verifica o tipo de token
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token inválido para esta operação.",
        )

    # Verifica se o token foi revogado (logout)
    jti = payload.get("jti")
    if jti and is_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revogado. Por favor, faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    usuario_id_str = payload.get("sub")
    if usuario_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token malformado: identificador de usuário ausente.",
        )

    try:
        return int(usuario_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identificador de usuário inválido.",
        )

