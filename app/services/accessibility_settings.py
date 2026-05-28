from uuid import UUID

from app.dtos.accessibility_settings import (
    AccessibilitySettingResponse,
    AccessibilitySettingUpdateRequest,
)
from app.repositories.accessibility_repository import AccessibilityRepository


class AccessibilityService:
    """접근성 설정 비즈니스 로직"""

    def __init__(self):
        self.repo = AccessibilityRepository()

    async def get_my_setting(self, user_id: UUID) -> AccessibilitySettingResponse:
        """내 설정 조회"""
        setting = await self.repo.get_by_user(user_id)
        if not setting:
            setting = await self.repo.create_or_update(user_id=user_id)
        return AccessibilitySettingResponse.model_validate(setting)

    async def update_my_setting(
        self, user_id: UUID, data: AccessibilitySettingUpdateRequest
    ) -> AccessibilitySettingResponse:
        """설정 업데이트"""
        setting = await self.repo.create_or_update(
            user_id=user_id,
            font_size=data.font_size,
            tts_enabled=data.tts_enabled,
            easy_language=data.easy_language,
            guardian_share_enabled=data.guardian_share_enabled,
        )
        return AccessibilitySettingResponse.model_validate(setting)
