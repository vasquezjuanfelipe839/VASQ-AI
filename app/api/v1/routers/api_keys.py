from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user
from app.application.schemas.api_key import (
    APIKeyCreatedResponse,
    APIKeyCreateRequest,
    APIKeyResponse,
)
from app.application.services.api_key_service import APIKeyError, APIKeyService
from app.infrastructure.db.models_user import User
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: APIKeyCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> APIKeyCreatedResponse:
    """
    Crea una nueva API Key para el usuario autenticado.

    La key en texto plano solo se devuelve en esta respuesta — guárdala,
    porque no se puede volver a consultar (solo se almacena su hash).
    """
    service = APIKeyService(db)
    api_key, plain_key = await service.create(
        owner_id=current_user.id,
        name=data.name,
        scopes=data.scopes,
        expires_in_days=data.expires_in_days,
    )
    return APIKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        prefix=api_key.prefix,
        plain_key=plain_key,
        scopes=api_key.scopes,
        expires_at=api_key.expires_at,
    )


@router.get("", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[APIKeyResponse]:
    service = APIKeyService(db)
    keys = await service.list_for_owner(current_user.id)
    return [APIKeyResponse.model_validate(k) for k in keys]


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    api_key_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    service = APIKeyService(db)
    try:
        await service.revoke(current_user.id, api_key_id)
    except APIKeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
