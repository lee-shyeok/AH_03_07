from uuid import UUID

from app.dtos.feedback_logs import (
    FeedbackCreateRequest,
    FeedbackListResponse,
    FeedbackResponse,
)
from app.repositories.feedback_repository import FeedbackRepository


class FeedbackService:
    """피드백 비즈니스 로직"""

    def __init__(self):
        self.repo = FeedbackRepository()

    async def create_feedback(self, user_id: UUID, data: FeedbackCreateRequest) -> FeedbackResponse:
        """피드백 등록"""
        feedback = await self.repo.create(
            user_id=user_id,
            target_type=data.target_type,
            target_id=data.target_id,
            feedback_type=data.feedback_type,
            rating=data.rating,
            comment=data.comment,
        )
        return FeedbackResponse.model_validate(feedback)

    async def get_my_feedbacks(self, user_id: UUID) -> FeedbackListResponse:
        """내 피드백 목록"""
        feedbacks = await self.repo.get_user_feedbacks(user_id)
        return FeedbackListResponse(
            feedbacks=[FeedbackResponse.model_validate(f) for f in feedbacks],
            total=len(feedbacks),
        )
