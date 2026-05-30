from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.security import get_request_user
from app.dtos.chat import (
    FeedbackRequest,
    FeedbackResponse,
    MessageHistoryResponse,
    MessageItem,
    MessageRequest,
    MessageResponse,
    RagSource,
    SessionStartResponse,
)
from app.models.users import User
from app.services.chat_feedback_service import ChatFeedbackService
from app.services.chat_message_service import ChatMessageService, get_chat_message_service
from app.services.chat_session_service import ChatSessionService

chat_router = APIRouter(prefix="/chat", tags=["chat"])


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


@chat_router.post("/messages/{message_id}/feedback", status_code=status.HTTP_200_OK)
async def submit_feedback(
    message_id: int,
    body: FeedbackRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChatFeedbackService, Depends(ChatFeedbackService)],
) -> FeedbackResponse:
    feedback = await service.record_feedback(user, message_id, body.score, body.comment)
    if feedback is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="메시지를 찾을 수 없습니다")
    return FeedbackResponse(
        message_id=message_id,
        score=feedback.score,
        recorded_at=feedback.created_at,
    )


@chat_router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def start_chat_session(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[ChatSessionService, Depends(ChatSessionService)],
) -> SessionStartResponse:
    session = await service.create_session(user)
    return SessionStartResponse(session_id=session.id)
