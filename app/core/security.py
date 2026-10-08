"""
Utilidades de seguridad compartidas: hashing de contraseñas y JWT.

Deliberadamente centralizado aquí para que solo haya un lugar donde se
decide el algoritmo de hashing y de firma de tokens. Si en el futuro se
quiere migrar a Argon2 en vez de bcrypt, por ejemplo, se cambia aquí y
en ningún otro sitio.
"""

from datetime import datetime, timedelta, timezone
from enum import Enum

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def create_token(subject: str, token_type: TokenType) -> str:
    """
    Crea un JWT firmado. `subject` es normalmente el id del usuario.
    El campo `type` dentro del token distingue access de refresh, para
    que un refresh token no pueda usarse como si fuera un access token.
    """
    now = datetime.now(timezone.utc)

    if token_type == TokenType.ACCESS:
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": subject,
        "type": token_type.value,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Lanza JWTError si el token es inválido, expiró o la firma no coincide."""
    try:
        return jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        raise
