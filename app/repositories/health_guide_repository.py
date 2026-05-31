from uuid import UUID

from app.models.health_guides import GuideStatus, HealthGuideContent


class HealthGuideRepository:
    @staticmethod
    async def get_user_guides(user_id: UUID) -> list[HealthGuideContent]:
        return await HealthGuideContent.filter(user_id=user_id).order_by("-created_at").all()

    @staticmethod
    async def get_by_id(guide_id: UUID) -> HealthGuideContent | None:
        return await HealthGuideContent.filter(id=guide_id).first()

    @staticmethod
    async def create(user_id: UUID, **kwargs) -> HealthGuideContent:
        return await HealthGuideContent.create(user_id=user_id, **kwargs)

    @staticmethod
    async def update_result(
        guide_id: UUID,
        guide_content: str,
        status: GuideStatus = GuideStatus.COMPLETED,
    ) -> HealthGuideContent | None:
        guide = await HealthGuideContent.filter(id=guide_id).first()
        if guide:
            guide.guide_content = guide_content
            guide.status = status
            await guide.save()
        return guide
