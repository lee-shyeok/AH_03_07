from datetime import datetime
from uuid import UUID

from openai import OpenAI

from app.core import config
from app.dtos.health_guides import (
    HealthGuideCreateRequest,
    HealthGuideListResponse,
    HealthGuideResponse,
)
from app.models.health_guides import GuideStatus
from app.models.notifications import NotificationType
from app.models.prompts import PromptType
from app.repositories.health_guide_repository import HealthGuideRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.prompt_repository import PromptRepository


class HealthGuideService:
    def __init__(self):
        self.repo = HealthGuideRepository()
        self.prompt_repo = PromptRepository()
        self.noti_repo = NotificationRepository()
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)

    async def get_my_guides(self, user_id: UUID) -> HealthGuideListResponse:
        guides = await self.repo.get_user_guides(user_id)
        return HealthGuideListResponse(
            guides=[HealthGuideResponse.model_validate(g) for g in guides],
            total=len(guides),
        )

    async def generate_guide(self, user_id: UUID, data: HealthGuideCreateRequest) -> HealthGuideResponse:
        """AI 가이드 생성!"""
        guide = await self.repo.create(
            user_id=user_id,
            guide_type=data.guide_type,
            user_question=data.user_question,
        )

        try:
            guide.status = GuideStatus.PROCESSING
            await guide.save()

            active_prompt = await self.prompt_repo.get_active(PromptType.HEALTH_GUIDE)

            if active_prompt:
                system_prompt = active_prompt.template_text
            else:
                system_prompt = "당신은 건강 가이드 전문가입니다. 사용자의 질문에 친절하고 정확하게 답변해주세요."

            response = self.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": data.user_question},
                ],
                max_tokens=1500,
            )

            guide_content = response.choices[0].message.content
            await self.repo.update_result(
                guide_id=guide.id,
                guide_content=guide_content,
                status=GuideStatus.COMPLETED,
            )
            guide = await self.repo.get_by_id(guide.id)

            # NOTI-003: 가이드 생성 완료 알림
            await self.noti_repo.create_notification(
                user_id=user_id,
                notification_type=NotificationType.GUIDE,
                title="새로운 맞춤 가이드가 도착했습니다",
                content="새로운 맞춤 가이드가 도착했습니다. 지금 확인해보세요!",
                scheduled_at=datetime.now(),
            )

        except Exception as e:
            await self.repo.update_result(
                guide_id=guide.id,
                guide_content=f"가이드 생성 실패: {str(e)}",
                status=GuideStatus.FAILED,
            )
            guide = await self.repo.get_by_id(guide.id)

        return HealthGuideResponse.model_validate(guide)
