from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field

from app.dependencies.security import get_request_user
from app.dtos.base import BaseSerializerModel
from app.models.users import User
from app.services.chat_service import chat_with_rag

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
