"""
Puerto de dominio: contrato para cualquier proveedor de modelo de lenguaje.

Esta es la pieza más importante de toda la arquitectura. Nada en el
sistema (servicios, routers) debe importar Ollama, OpenAI o cualquier
SDK concreto directamente — todos dependen de esta interfaz. Cambiar de
modelo de IA en el futuro significa escribir una nueva clase que
implemente `LLMProvider` y apuntar `LLM_PROVIDER` a ella; cero cambios
en el resto del código.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """Un mensaje dentro del historial de una conversación."""

    role: MessageRole
    content: str


@dataclass
class LLMResponse:
    """Respuesta normalizada de cualquier proveedor de LLM."""

    content: str
    model: str
    provider: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    raw: dict = field(default_factory=dict)  # payload crudo, útil para depurar


class LLMProviderError(Exception):
    """Error genérico al comunicarse con un proveedor de LLM."""


class LLMProvider(ABC):
    """
    Contrato que debe cumplir cualquier proveedor de modelo de lenguaje
    (Ollama, OpenAI, Anthropic, Gemini, etc.).
    """

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Genera una respuesta completa a partir del historial de mensajes."""
        raise NotImplementedError

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Genera la respuesta en streaming, entregando fragmentos de texto."""
        raise NotImplementedError
        yield  # pragma: no cover - hace de este método un generador para mypy

    @abstractmethod
    async def health_check(self) -> bool:
        """Indica si el proveedor está disponible y listo para responder."""
        raise NotImplementedError
