"""
Dependencias reutilizables inyectadas en los endpoints de la API v1.

Centralizar esto aquí evita repetir `Depends(...)` largos en cada router
y es el lugar donde se traduce "token JWT válido" -> "objeto User".
"""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenType, decode_token
from app.infrastructure.db.models_api_key import APIKey
from app.infrastructure.db.models_user import User
from app.infrastructure.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
    except JWTError:
        raise credentials_exception

    if payload.get("type") != TokenType.ACCESS.value:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    from app.application.services.auth_service import AuthService

    user = await AuthService(db).get_user_by_id(user_id)
    if user is None or not user.is_active:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo.")
    return current_user


def require_api_key(required_scope: str | None = None):
    """
    Dependencia para endpoints pensados para consumidores programáticos
    (otros servicios de VASQTECH, integraciones externas), autenticados
    por API Key en el header `X-API-Key` en vez de JWT.

    Uso: `Depends(require_api_key("chat:write"))`.
    """

    async def _dependency(
        db: Annotated[AsyncSession, Depends(get_db)],
        x_api_key: Annotated[str | None, Header()] = None,
    ) -> APIKey:
        if not x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Falta el header X-API-Key.",
            )

        from app.application.services.api_key_service import APIKeyService

        api_key = await APIKeyService(db).validate(x_api_key)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API Key inválida, revocada o expirada.",
            )

        if required_scope and required_scope not in api_key.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Esta API Key no tiene el scope requerido: {required_scope}",
            )

        return api_key

    return _dependency
