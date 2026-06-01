from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.dependencies.security import get_request_user
from app.dtos.chat_stream import StreamMessageRequest
from app.models.users import User
from app.services.chat_session_service import ChatSessionService
from app.services.chat_stream_service import ChatStreamService

chat_stream_router = APIRouter(prefix="/chat", tags=["chat-stream"])


@chat_stream_router.post(
    "/sessions/{session_id}/messages/stream",
    status_code=status.HTTP_200_OK,
)
async def stream_chat_message(
    session_id: int,
    body: StreamMessageRequest,
    user: Annotated[User, Depends(get_request_user)],
    session_service: Annotated[ChatSessionService, Depends(ChatSessionService)],
) -> StreamingResponse:
    session = await session_service.get_user_session(user, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="세션을 찾을 수 없습니다")
    service = ChatStreamService()
    if service.is_session_expired(session):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="세션이 만료되었습니다")
    return StreamingResponse(
        service.stream_message(session, user, body.message),
        media_type="text/event-stream",
    )
