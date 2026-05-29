from datetime import datetime
from uuid import UUID

from app.models.notification_settings import NotificationSetting
from app.models.notifications import Notification, NotificationType


class NotificationRepository:
    """알림 DB 쿼리"""

    @staticmethod
    async def get_user_setting(user_id: UUID) -> NotificationSetting | None:
        """사용자 알림 설정 조회"""
        return await NotificationSetting.filter(user_id=user_id).first()

    @staticmethod
    async def create_or_update_setting(user_id: UUID, **kwargs) -> NotificationSetting:
        """알림 설정 생성/수정"""
        setting = await NotificationSetting.filter(user_id=user_id).first()
        if setting:
            for key, value in kwargs.items():
                setattr(setting, key, value)
            await setting.save()
            return setting
        return await NotificationSetting.create(user_id=user_id, **kwargs)

    @staticmethod
    async def get_user_notifications(user_id: UUID) -> list[Notification]:
        """사용자 알림 목록"""
        return await Notification.filter(user_id=user_id).order_by("-created_at").all()

    @staticmethod
    async def mark_as_read(notification_id: UUID) -> Notification | None:
        """알림 읽음 처리"""
        notification = await Notification.filter(id=notification_id).first()
        if notification:
            notification.read_at = datetime.now()
            await notification.save()
        return notification

    @staticmethod
    async def create_notification(
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        content: str,
        scheduled_at: datetime,
    ) -> Notification:
        """알림 생성"""
        return await Notification.create(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            content=content,
            scheduled_at=scheduled_at,
        )
