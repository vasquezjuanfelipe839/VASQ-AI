"""
Factory de proveedores de LLM.

Este es el ÚNICO lugar del proyecto que decide, según `settings.LLM_PROVIDER`,
qué implementación concreta de `LLMProvider` se usa. Todo lo demás (servicios,
routers) recibe siempre la interfaz abstracta vía inyección de dependencias
de FastAPI (ver app/api/v1/deps.py) y nunca sabe qué proveedor hay detrás.

Para añadir un proveedor nuevo:
1. Crear la clase en infrastructure/llm/<nombre>_provider.py implementando LLMProvider.
2. Añadir un `elif` aquí.
3. Añadir sus variables de config en app/core/config.py y .env.example.
Nada más se toca.
"""

from functools import lru_cache

from app.core.config import settings
from app.domain.ports.llm_provider import LLMProvider
from app.infrastructure.llm.ollama_provider import OllamaProvider
from app.infrastructure.llm.openai_provider import OpenAIProvider


def _build_provider() -> LLMProvider:
    provider_name = settings.LLM_PROVIDER.lower()

    if provider_name == "ollama":
        return OllamaProvider(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
        )

    if provider_name == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY no está configurada en .env")
        return OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
        )

    # Cuando se implemente AnthropicProvider, se añade aquí de la misma forma:
    # if provider_name == "anthropic":
    #     return AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY, model=settings.ANTHROPIC_MODEL)

    raise ValueError(
        f"LLM_PROVIDER '{provider_name}' no reconocido. "
        f"Valores soportados: ollama, openai."
    )


@lru_cache
def get_llm_provider() -> LLMProvider:
    """
    Devuelve una instancia cacheada del proveedor de LLM configurado.

    Se inyecta en los endpoints con `Depends(get_llm_provider)`.
    """
    return _build_provider()
