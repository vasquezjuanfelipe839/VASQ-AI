"""
Configuración central de VASQ AI.

Todo lo que pueda variar entre entornos (local, staging, producción) o entre
proveedores de LLM vive aquí, leído desde variables de entorno. Ningún otro
módulo del proyecto debe leer os.environ directamente: siempre se importa
`settings` desde este archivo. Esto es lo que nos permite, por ejemplo,
cambiar de Ollama a OpenAI sin tocar una sola línea de lógica de negocio.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Metadatos de la app ---
    APP_NAME: str = "VASQ AI"
    APP_ENV: str = "local"  # local | staging | production
    DEBUG: bool = True

    # --- Seguridad / JWT ---
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_ENV"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- API Keys propias ---
    API_KEY_PREFIX: str = "vasq_"

    # --- Base de datos ---
    DATABASE_URL: str = "postgresql+psycopg://vasq:vasq@localhost:5432/vasq_ai"

    # --- Redis (opcional) ---
    REDIS_ENABLED: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Proveedor de LLM ---
    # Esta es la variable clave para intercambiar el modelo de IA sin tocar
    # código: "ollama" hoy, "openai" | "anthropic" | "gemini" en el futuro.
    LLM_PROVIDER: str = "ollama"

    # Config específica de Ollama (usada solo si LLM_PROVIDER=ollama)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3"

    # Config específica de OpenAI (reservado para cuando se implemente el provider)
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o"

    # Config específica de Anthropic (reservado para cuando se implemente el provider)
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Devuelve una instancia cacheada de Settings.

    Se usa @lru_cache para que el .env solo se lea una vez por proceso,
    y para poder inyectar `get_settings` como dependencia de FastAPI
    (facilita también el mockeo en tests).
    """
    return Settings()


settings = get_settings()
