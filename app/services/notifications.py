from fastapi import HTTPException, status

from app.dtos.notifications import (
    NotificationListResponse,
    NotificationResponse,
    NotificationSettingResponse,
    NotificationSettingUpdateRequest,
)
from app.repositories.notification_repository import NotificationRepository


class NotificationService:
    """알림 비즈니스 로직"""

    def __init__(self):
        self.repo = NotificationRepository()

    async def get_my_setting(self, user_id: int) -> NotificationSettingResponse:
        """내 알림 설정 조회"""
        setting = await self.repo.get_user_setting(user_id)
        if not setting:
            # 없으면 기본 설정으로 생성
            setting = await self.repo.create_or_update_setting(user_id=user_id)
        return NotificationSettingResponse.model_validate(setting)

    async def update_my_setting(
        self, user_id: int, data: NotificationSettingUpdateRequest
    ) -> NotificationSettingResponse:
        """내 알림 설정 수정"""
        setting = await self.repo.create_or_update_setting(
            user_id=user_id,
            **data.model_dump(),
        )
        return NotificationSettingResponse.model_validate(setting)

    async def get_my_notifications(self, user_id: int) -> NotificationListResponse:
        """내 알림 목록 조회"""
        notifications = await self.repo.get_user_notifications(user_id)
        return NotificationListResponse(
            notifications=[NotificationResponse.model_validate(n) for n in notifications],
            total=len(notifications),
        )

    async def mark_as_read(self, user_id: int, notification_id: int) -> NotificationResponse:
        """알림 읽음 처리"""
        notification = await self.repo.mark_as_read(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="알림을 찾을 수 없습니다.",
            )
        if notification.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="권한이 없습니다.",
            )
        return NotificationResponse.model_validate(notification)
