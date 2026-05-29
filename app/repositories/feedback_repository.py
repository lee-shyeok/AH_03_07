from uuid import UUID

from app.models.feedback_logs import FeedbackLog


class FeedbackRepository:
    """피드백 DB 쿼리"""

    @staticmethod
    async def create(user_id: UUID, **kwargs) -> FeedbackLog:
        """피드백 생성"""
        return await FeedbackLog.create(user_id=user_id, **kwargs)

    @staticmethod
    async def get_user_feedbacks(user_id: UUID) -> list[FeedbackLog]:
        """사용자 피드백 목록"""
        return await FeedbackLog.filter(user_id=user_id).order_by("-created_at").all()

    @staticmethod
    async def get_by_target(target_id: UUID) -> list[FeedbackLog]:
        """특정 대상의 피드백 목록"""
        return await FeedbackLog.filter(target_id=target_id).order_by("-created_at").all()
