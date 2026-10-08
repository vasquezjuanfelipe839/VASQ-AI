"""
Logging centralizado.

Usamos el módulo `logging` estándar de Python configurado una sola vez
al arrancar la app (ver app/main.py). Cualquier módulo obtiene su logger
con `logging.getLogger(__name__)` y hereda esta configuración.
"""

import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    level = logging.DEBUG if settings.DEBUG else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    # Bajamos el ruido de librerías muy verbosas
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )
