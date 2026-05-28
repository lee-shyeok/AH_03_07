from uuid import UUID

from app.models.accessibility_settings import AccessibilitySetting


class AccessibilityRepository:
    """접근성 설정 DB 쿼리"""

    @staticmethod
    async def get_by_user(user_id: UUID) -> AccessibilitySetting | None:
        """사용자 접근성 설정 조회"""
        return await AccessibilitySetting.filter(user_id=user_id).first()

    @staticmethod
    async def create_or_update(user_id: UUID, **kwargs) -> AccessibilitySetting:
        """설정 생성/수정"""
        setting = await AccessibilitySetting.filter(user_id=user_id).first()
        if setting:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(setting, key, value)
            await setting.save()
            return setting
        return await AccessibilitySetting.create(user_id=user_id, **kwargs)
