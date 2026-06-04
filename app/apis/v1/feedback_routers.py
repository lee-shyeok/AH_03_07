from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies.security import get_request_user
from app.dtos.feedback_logs import (
    FeedbackCreateRequest,
    FeedbackListResponse,
    FeedbackResponse,
)
from app.models.users import User
from app.services.feedback_logs import FeedbackService

feedback_router = APIRouter(prefix="/feedback", tags=["feedback"])


@feedback_router.get("", response_model=FeedbackListResponse)
async def get_my_feedbacks(
    user: Annotated[User, Depends(get_request_user)],
):
    """내 피드백 목록"""
    service = FeedbackService()
    return await service.get_my_feedbacks(user.id)


@feedback_router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    data: FeedbackCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
):
    """피드백 등록"""
    service = FeedbackService()
    return await service.create_feedback(user.id, data)
