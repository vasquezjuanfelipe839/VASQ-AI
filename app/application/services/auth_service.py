"""
Caso de uso: autenticación de usuarios.

Este servicio no sabe nada de FastAPI ni de HTTP — recibe una sesión de
DB y datos ya validados, y devuelve entidades de dominio o lanza
excepciones de negocio. Los routers son los que traducen esto a
respuestas HTTP (ver app/api/v1/routers/auth.py).
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenType, create_token, hash_password, verify_password
from app.infrastructure.db.models_user import User


class AuthError(Exception):
    """Error de negocio en el flujo de autenticación (credenciales, duplicados, etc.)."""


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def register(self, email: str, password: str, full_name: str | None) -> User:
        existing = await self._db.scalar(select(User).where(User.email == email))
        if existing:
            raise AuthError("Ya existe un usuario registrado con ese email.")

        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
        )
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> User:
        user = await self._db.scalar(select(User).where(User.email == email))
        if not user or not verify_password(password, user.hashed_password):
            raise AuthError("Email o contraseña incorrectos.")
        if not user.is_active:
            raise AuthError("Esta cuenta está desactivada.")
        return user

    @staticmethod
    def issue_tokens(user: User) -> tuple[str, str]:
        access_token = create_token(str(user.id), TokenType.ACCESS)
        refresh_token = create_token(str(user.id), TokenType.REFRESH)
        return access_token, refresh_token

    async def refresh_access_token(self, user_id: str) -> str:
        """Se llama después de validar el refresh token en el router."""
        return create_token(user_id, TokenType.ACCESS)

    async def get_user_by_id(self, user_id: str) -> User | None:
        return await self._db.scalar(select(User).where(User.id == user_id))
