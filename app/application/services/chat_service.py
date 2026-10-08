"""
Caso de uso: enviar un mensaje de chat y obtener respuesta del modelo.

Este servicio es el corazón de la orquestación, y fíjate que NO importa
Ollama en ningún lado — solo conoce la interfaz `LLMProvider`. Eso es lo
que hace posible que, cambiando únicamente `LLM_PROVIDER` en `.env`,
este archivo siga funcionando exactamente igual con GPT o Claude detrás.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.memory_service import MemoryService
from app.domain.ports.llm_provider import LLMProvider, LLMProviderError, Message, MessageRole
from app.infrastructure.db.models_chat import ChatMessage, Conversation


class ChatError(Exception):
    """Error de negocio en el flujo de chat."""


class ChatService:
    def __init__(self, db: AsyncSession, llm_provider: LLMProvider) -> None:
        self._db = db
        self._llm = llm_provider
        self._memory = MemoryService(db)

    async def send_message(
        self,
        owner_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
        user_message: str,
        temperature: float = 0.7,
    ) -> tuple[Conversation, ChatMessage]:
        try:
            conversation = await self._memory.get_or_create_conversation(
                owner_id, conversation_id
            )
        except ValueError as exc:
            raise ChatError(str(exc)) from exc

        # 1. Recuperar historial (memoria conversacional)
        history = await self._memory.get_history_as_messages(conversation.id)

        # 2. Guardar el mensaje del usuario
        await self._memory.append_message(conversation.id, MessageRole.USER, user_message)
        history.append(Message(role=MessageRole.USER, content=user_message))

        # 3. Llamar al proveedor de LLM configurado (Ollama/Qwen 3 hoy)
        try:
            llm_response = await self._llm.generate(history, temperature=temperature)
        except LLMProviderError as exc:
            raise ChatError(f"El modelo de IA no pudo responder: {exc}") from exc

        # 4. Guardar la respuesta del asistente
        assistant_message = await self._memory.append_message(
            conversation.id,
            MessageRole.ASSISTANT,
            llm_response.content,
            prompt_tokens=llm_response.prompt_tokens,
            completion_tokens=llm_response.completion_tokens,
        )

        return conversation, assistant_message
