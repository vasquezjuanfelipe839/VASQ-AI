"""
Implementación de LLMProvider que habla con un servidor Ollama local.

Este es el único archivo del proyecto que sabe que existe algo llamado
"Ollama" o "Qwen 3". Si mañana quieres usar GPT o Claude, escribes
`openai_provider.py` / `anthropic_provider.py` con la misma interfaz y
no tocas nada más (ver factory.py).
"""

import logging
from collections.abc import AsyncIterator

import httpx

from app.domain.ports.llm_provider import (
    LLMProvider,
    LLMProviderError,
    LLMResponse,
    Message,
)

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str, model: str, timeout: float = 120.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    def _to_ollama_messages(self, messages: list[Message]) -> list[dict]:
        return [{"role": m.role.value, "content": m.content} for m in messages]

    async def generate(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        payload = {
            "model": self._model,
            "messages": self._to_ollama_messages(messages),
            "stream": False,
            "options": {
                "temperature": temperature,
                **({"num_predict": max_tokens} if max_tokens else {}),
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/api/chat", json=payload
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            logger.error("Error al llamar a Ollama: %s", exc)
            raise LLMProviderError(f"Ollama no respondió correctamente: {exc}") from exc

        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=self._model,
            provider="ollama",
            prompt_tokens=data.get("prompt_eval_count"),
            completion_tokens=data.get("eval_count"),
            raw=data,
        )

    async def generate_stream(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        payload = {
            "model": self._model,
            "messages": self._to_ollama_messages(messages),
            "stream": True,
            "options": {
                "temperature": temperature,
                **({"num_predict": max_tokens} if max_tokens else {}),
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                async with client.stream(
                    "POST", f"{self._base_url}/api/chat", json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        import json

                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if chunk.get("done"):
                            break
        except httpx.HTTPError as exc:
            logger.error("Error en streaming con Ollama: %s", exc)
            raise LLMProviderError(f"Ollama no respondió correctamente: {exc}") from exc

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                return response.status_code == 200
        except httpx.HTTPError:
            return False
