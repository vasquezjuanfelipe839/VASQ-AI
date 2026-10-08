from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user
from app.application.schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ConversationDetailResponse,
    ConversationResponse,
)
from app.application.services.chat_service import ChatError, ChatService
from app.application.services.memory_service import MemoryService
from app.core.config import settings
from app.domain.ports.llm_provider import LLMProvider
from app.infrastructure.db.models_user import User
from app.infrastructure.db.session import get_db
from app.infrastructure.llm.factory import get_llm_provider

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def send_chat_message(
    data: ChatRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    llm: Annotated[LLMProvider, Depends(get_llm_provider)],
) -> ChatResponse:
    """
    Envía un mensaje al asistente. Si no se pasa `conversation_id`, se crea
    una conversación nueva. El historial se recupera automáticamente de
    PostgreSQL para dar contexto al modelo (memoria conversacional).
    """
    service = ChatService(db, llm)
    try:
        conversation, assistant_message = await service.send_message(
            owner_id=current_user.id,
            conversation_id=data.conversation_id,
            user_message=data.message,
            temperature=data.temperature,
        )
    except ChatError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ChatResponse(
        conversation_id=conversation.id,
        message=ChatMessageResponse.model_validate(assistant_message),
        model=settings.OLLAMA_MODEL if settings.LLM_PROVIDER == "ollama" else "unknown",
        provider=settings.LLM_PROVIDER,
    )


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ConversationResponse]:
    conversations = await MemoryService(db).list_conversations(current_user.id)
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationDetailResponse:
    conversation = await MemoryService(db).get_conversation_with_messages(
        current_user.id, conversation_id
    )
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversación no encontrada.")
    return ConversationDetailResponse.model_validate(conversation)
