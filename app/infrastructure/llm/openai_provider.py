"""
Placeholder para un futuro proveedor OpenAI.

Deliberadamente no implementado todavía: existe para dejar claro dónde
va el código el día que se active `LLM_PROVIDER=openai`. La firma ya
cumple el contrato de `LLMProvider`, así que activar este proveedor no
requerirá cambios en factory.py, servicios ni routers.
"""

from collections.abc import AsyncIterator

from app.domain.ports.llm_provider import LLMProvider, LLMResponse, Message


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def generate(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        raise NotImplementedError(
            "OpenAIProvider aún no está implementado. "
            "Cuando se active, deberá usar el SDK oficial de OpenAI "
            "respetando el contrato de LLMProvider."
        )

    async def generate_stream(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        raise NotImplementedError("OpenAIProvider aún no está implementado.")
        yield  # pragma: no cover

    async def health_check(self) -> bool:
        return False
