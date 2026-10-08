"""
Caso de uso: gestión de API Keys propias.

Las keys se generan con secrets.token_urlsafe (criptográficamente
seguras), se muestran en texto plano UNA sola vez al crearlas, y se
guardan siempre hasheadas (bcrypt) — igual que las contraseñas. Un
prefijo corto y no sensible se guarda aparte para poder identificarlas
en un listado sin exponer el secreto.
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.infrastructure.db.models_api_key import APIKey


class APIKeyError(Exception):
    """Error de negocio en el flujo de API Keys."""


class APIKeyService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        owner_id: uuid.UUID,
        name: str,
        scopes: list[str],
        expires_in_days: int | None = None,
    ) -> tuple[APIKey, str]:
        raw_secret = secrets.token_urlsafe(32)
        plain_key = f"{settings.API_KEY_PREFIX}{raw_secret}"
        visible_prefix = plain_key[: len(settings.API_KEY_PREFIX) + 8]

        expires_at = (
            datetime.now(timezone.utc) + timedelta(days=expires_in_days)
            if expires_in_days
            else None
        )

        api_key = APIKey(
            hashed_key=hash_password(plain_key),
            prefix=visible_prefix,
            name=name,
            scopes=scopes,
            owner_id=owner_id,
            expires_at=expires_at,
        )
        self._db.add(api_key)
        await self._db.commit()
        await self._db.refresh(api_key)

        # plain_key solo se devuelve aquí; nunca se vuelve a poder consultar.
        return api_key, plain_key

    async def list_for_owner(self, owner_id: uuid.UUID) -> list[APIKey]:
        result = await self._db.scalars(
            select(APIKey).where(APIKey.owner_id == owner_id).order_by(APIKey.created_at.desc())
        )
        return list(result.all())

    async def revoke(self, owner_id: uuid.UUID, api_key_id: uuid.UUID) -> None:
        api_key = await self._db.scalar(
            select(APIKey).where(APIKey.id == api_key_id, APIKey.owner_id == owner_id)
        )
        if not api_key:
            raise APIKeyError("API Key no encontrada.")
        api_key.is_active = False
        await self._db.commit()

    async def validate(self, plain_key: str) -> APIKey | None:
        """
        Valida una API Key recibida en un request.

        Nota de rendimiento: como el hash es bcrypt (no determinista),
        no se puede buscar directamente por hashed_key en la DB. Por eso
        se filtra primero por prefijo (indexado) y luego se verifica con
        bcrypt solo contra ese subconjunto pequeño de candidatos.
        """
        prefix = plain_key[: len(settings.API_KEY_PREFIX) + 8]
        candidates = await self._db.scalars(
            select(APIKey).where(APIKey.prefix == prefix, APIKey.is_active.is_(True))
        )

        now = datetime.now(timezone.utc)
        for candidate in candidates:
            if candidate.expires_at and candidate.expires_at < now:
                continue
            if verify_password(plain_key, candidate.hashed_key):
                candidate.last_used_at = now
                await self._db.commit()
                return candidate
        return None
