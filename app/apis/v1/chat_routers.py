from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field

from app.dependencies.security import get_request_user
from app.dtos.base import BaseSerializerModel
from app.dtos.chat import (
    MessageHistoryResponse,
    MessageItem,
    MessageRequest,
    MessageResponse,
    RagSource,
    SessionStartResponse,
)
from app.models.users import User
from app.services.chat_message_service import ChatMessageService, get_chat_message_service
from app.services.chat_service import chat_with_rag
from app.services.chat_session_service import ChatSessionService

chat_router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseSerializerModel):
    message: str = Field(min_length=1, max_length=1000)


class ChatSource(BaseSerializerModel):
    title: str
    section: str | None
    page: int
    organization: str
    published_year: int
    score: float


class ChatResponse(BaseSerializerModel):
    answer: str
    is_general_info: bool
    sources: list[ChatSource]


@chat_router.post("/sessions/{session_id}/messages", status_code=status.HTTP_200_OK)
async def create_chat_message(
    session_id: int,
    body: MessageRequest,
    user: Annotated[User, Depends(get_request_user)],
    session_service: Annotated[ChatSessionService, Depends(ChatSessionService)],
    message_service: Annotated[ChatMessageService, Depends(get_chat_message_service)],
) -> MessageResponse:
    session = await session_service.get_user_session(user, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="세션을 찾을 수 없습니다")
    message = await message_service.handle_message(session, body.content)
    return MessageResponse(
        message_id=message.id,
        role=message.role,
        content=message.content,
        rag_sources=[RagSource(**s) for s in message.rag_sources],
        blocked_by_filter=message.blocked_by_filter,
        block_reason=message.block_reason,
    )


@chat_router.get("/sessions/{session_id}/messages", status_code=status.HTTP_200_OK)
async def list_chat_messages(
    session_id: int,
    user: Annotated[User, Depends(get_request_user)],
    session_service: Annotated[ChatSessionService, Depends(ChatSessionService)],
    message_service: Annotated[ChatMessageService, Depends(get_chat_message_service)],
    page: int = 1,
    size: int = 20,
) -> MessageHistoryResponse:
    session = await session_service.get_user_session(user, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="세션을 찾을 수 없습니다")
    messages, total = await message_service.get_messages(session, page, size)
    return MessageHistoryResponse(
        items=[MessageItem.model_validate(m) for m in messages],
        page=page,
        size=size,
        total=total,
    )


@chat_router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def start_chat_session(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChatSessionService, Depends(ChatSessionService)],
) -> SessionStartResponse:
    session = await service.create_session(user)
    return SessionStartResponse(session_id=session.id)


@chat_router.post("", status_code=status.HTTP_200_OK)
async def chat(
    body: ChatRequest,
    user: Annotated[User, Depends(get_request_user)],
) -> ChatResponse:
    try:
        result = await chat_with_rag(body.message)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return ChatResponse(
        answer=result["answer"],
        is_general_info=result["is_general_info"],
        sources=[ChatSource(**s) for s in result["sources"]],
    )
