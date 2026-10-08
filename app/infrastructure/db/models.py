"""
Punto único de importación de todos los modelos ORM.

Alembic (y cualquier `Base.metadata.create_all`) necesita que todos los
modelos hayan sido importados al menos una vez para registrarse en
`Base.metadata`. Este archivo existe solo para eso — importa aquí
cualquier modelo nuevo que crees.
"""

from app.infrastructure.db.models_api_key import APIKey  # noqa: F401
from app.infrastructure.db.models_chat import ChatMessage, Conversation  # noqa: F401
from app.infrastructure.db.models_user import User  # noqa: F401
from app.infrastructure.db.session import Base  # noqa: F401
