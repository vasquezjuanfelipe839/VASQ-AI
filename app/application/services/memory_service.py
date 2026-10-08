"""
Caso de uso: memoria conversacional.

Hoy la "memoria" es simplemente recuperar los últimos N mensajes de
PostgreSQL e inyectarlos como contexto en cada llamada al LLMProvider.
Es intencionalmente simple. Si más adelante se quiere memoria semántica
(embeddings + búsqueda vectorial para recordar cosas de conversaciones
antiguas, no solo las últimas), se añade como una nueva capa dentro de
este mismo servicio, sin que ChatService ni los routers se enteren.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.ports.llm_provider import Message, MessageRole
from app.infrastructure.db.models_chat import ChatMessage, Conversation

DEFAULT_HISTORY_LIMIT = 20
SYSTEM_PROMPT = (
    "Eres el asistente de VASQ AI, la plataforma de inteligencia artificial "
    "de VASQTECH. Responde de forma clara, profesional y directa."
)


class MemoryService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_or_create_conversation(
        self, owner_id: uuid.UUID, conversation_id: uuid.UUID | None
    ) -> Conversation:
        if conversation_id:
            conversation = await self._db.scalar(
                select(Conversation).where(
                    Conversation.id == conversation_id, Conversation.owner_id == owner_id
                )
            )
            if not conversation:
                raise ValueError("Conversación no encontrada.")
            return conversation

        conversation = Conversation(owner_id=owner_id)
        self._db.add(conversation)
        await self._db.commit()
        await self._db.refresh(conversation)
        return conversation

    async def get_history_as_messages(
        self, conversation_id: uuid.UUID, limit: int = DEFAULT_HISTORY_LIMIT
    ) -> list[Message]:
        result = await self._db.scalars(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        rows = list(result.all())[::-1]  # orden cronológico ascendente

        history = [Message(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT)]
        history.extend(Message(role=MessageRole(row.role), content=row.content) for row in rows)
        return history

    async def append_message(
        self,
        conversation_id: uuid.UUID,
        role: MessageRole,
        content: str,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
    ) -> ChatMessage:
        message = ChatMessage(
            conversation_id=conversation_id,
            role=role.value,
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        self._db.add(message)
        await self._db.commit()
        await self._db.refresh(message)
        return message

    async def get_conversation_with_messages(
        self, owner_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> Conversation | None:
        return await self._db.scalar(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id, Conversation.owner_id == owner_id)
        )

    async def list_conversations(self, owner_id: uuid.UUID) -> list[Conversation]:
        result = await self._db.scalars(
            select(Conversation)
            .where(Conversation.owner_id == owner_id)
            .order_by(Conversation.updated_at.desc())
        )
        return list(result.all())
