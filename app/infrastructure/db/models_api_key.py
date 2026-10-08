"""Modelo ORM para las API Keys propias del sistema."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.session import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Solo guardamos el hash de la key, nunca la key en texto plano.
    hashed_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # Prefijo visible (ej. "vasq_ab12") para que el usuario identifique la key en un listado
    # sin exponer el secreto completo.
    prefix: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # etiqueta puesta por el usuario
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    owner: Mapped["User"] = relationship(back_populates="api_keys")  # noqa: F821

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
