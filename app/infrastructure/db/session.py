"""
Conexión a PostgreSQL vía SQLAlchemy (async).

Esta pieza es pura infraestructura: nadie fuera de `infrastructure/db`
debería importar `engine` directamente. El resto del sistema recibe una
sesión a través de la dependencia `get_db` (ver app/api/v1/deps.py, que
se añadirá en el Módulo 3 junto con Auth).
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# SQLAlchemy async requiere el driver async (psycopg en modo async o asyncpg).
# Usamos psycopg3 en modo async: postgresql+psycopg://...
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos ORM del proyecto."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia de FastAPI: entrega una sesión de DB por request."""
    async with AsyncSessionLocal() as session:
        yield session
