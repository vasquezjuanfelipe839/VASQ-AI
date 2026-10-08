import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class APIKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    scopes: list[str] = Field(default_factory=lambda: ["chat:read", "chat:write"])
    expires_in_days: int | None = None


class APIKeyCreatedResponse(BaseModel):
    """
    Se devuelve UNA sola vez, en el momento de crear la key.
    Después de esto, la key en texto plano no se puede volver a recuperar
    — solo se guarda su hash.
    """

    id: uuid.UUID
    name: str
    prefix: str
    plain_key: str
    scopes: list[str]
    expires_at: datetime | None


class APIKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    prefix: str
    scopes: list[str]
    is_active: bool
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
