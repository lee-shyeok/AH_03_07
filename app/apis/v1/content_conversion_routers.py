from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies.security import get_request_user
from app.dtos.content_conversions import (
    CardNewsCreateRequest,
    ContentConversionResponse,
)
from app.models.users import User
from app.services.content_conversions import ContentConversionService

content_router = APIRouter(prefix="/content", tags=["content"])


@content_router.post("/card-news", response_model=ContentConversionResponse, status_code=status.HTTP_201_CREATED)
async def create_card_news(
    data: CardNewsCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
):
    """카드뉴스 생성 (CONT-001)"""
    service = ContentConversionService()
    return await service.create_card_news(user.id, data.guide_id)


@content_router.post("/tts", response_model=ContentConversionResponse, status_code=status.HTTP_201_CREATED)
async def create_tts(
    data: CardNewsCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
):
    """가이드 → 음성 변환 (CONT-002)"""
    service = ContentConversionService()
    return await service.create_tts(user.id, data.guide_id)
