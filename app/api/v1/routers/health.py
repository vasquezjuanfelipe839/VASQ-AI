from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import settings
from app.domain.ports.llm_provider import LLMProvider
from app.infrastructure.llm.factory import get_llm_provider

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Chequeo básico de vida del servicio (no depende de servicios externos)."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "llm_provider": settings.LLM_PROVIDER,
    }


@router.get("/health/llm")
async def llm_health_check(
    llm: Annotated[LLMProvider, Depends(get_llm_provider)],
) -> dict:
    """
    Verifica que el proveedor de LLM configurado (Ollama u otro) esté
    respondiendo. Útil para detectar, por ejemplo, que Ollama no ha
    arrancado o que el modelo Qwen 3 aún no se ha descargado.
    """
    is_healthy = await llm.health_check()
    return {
        "provider": settings.LLM_PROVIDER,
        "healthy": is_healthy,
    }
