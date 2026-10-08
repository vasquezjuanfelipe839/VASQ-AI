"""
Módulo de trading (placeholder).

Este módulo está deliberadamente vacío de lógica de negocio — existe
para mostrar el patrón que deben seguir los módulos futuros (finance,
news, documents, automation, etc.):

1. Vive aislado en app/modules/<nombre>/, con su propio router,
   schemas y servicios.
2. Reutiliza las piezas del core (get_db, get_current_active_user,
   get_llm_provider) por inyección de dependencias — nunca duplica esa
   lógica.
3. Se registra en app/main.py con una sola línea, sin tocar el resto
   del sistema.

Cuando se implemente trading de verdad, esta carpeta tendrá su propia
estructura interna (routers.py, services.py, schemas.py, models.py)
igual que el core.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.deps import get_current_active_user
from app.infrastructure.db.models_user import User

router = APIRouter(prefix="/modules/trading", tags=["trading"])


@router.get("/status")
async def trading_module_status(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Endpoint de ejemplo: confirma que el módulo está montado y que la
    autenticación del core funciona igual aquí que en cualquier otro módulo."""
    return {
        "module": "trading",
        "status": "placeholder — sin lógica de negocio implementada todavía",
        "authenticated_as": current_user.email,
    }
