"""
Punto de entrada de VASQ AI.

Este archivo solo se encarga de ensamblar la aplicación FastAPI: configurar
logging, registrar routers y middlewares. No debe contener lógica de
negocio — esa vive en application/services, y el acceso a IA/DB vive en
infrastructure/. Así, main.py se mantiene simple sin importar cuánto
crezca el proyecto.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.routers import api_keys, auth, chat, health
from app.core.config import settings
from app.core.logging import configure_logging
from app.modules.trading.router import router as trading_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    # Aquí se añadirán en módulos futuros: verificación de conexión a DB,
    # precarga del LLMProvider, conexión a Redis, etc.
    yield
    # Shutdown: cierre limpio de conexiones (se completará en módulos futuros)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="Plataforma de IA modular y escalable de VASQTECH",
        version="0.1.0",
        lifespan=lifespan,
    )

    # --- Routers ---
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(api_keys.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")

    # Módulos de negocio (trading, finance, news, documents...) se registran
    # aquí siguiendo el mismo patrón de una sola línea. `trading` es el
    # ejemplo de referencia — sin lógica real todavía, solo la estructura.
    app.include_router(trading_router, prefix="/api/v1")

    return app


app = create_app()
