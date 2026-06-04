import logging
from datetime import datetime

from fastapi import HTTPException, status

from app.dtos.emergency_cards import (
    EmergencyCardCreateRequest,
    EmergencyCardResponse,
    SOSTriggerRequest,
    SOSTriggerResponse,
)
from app.models.audit_log import AuditLog
from app.models.guardians import Guardian
from app.models.notifications import Notification, NotificationType
from app.repositories.emergency_card_repository import EmergencyCardRepository

logger = logging.getLogger(__name__)


class EmergencyCardService:
    """응급 카드 비즈니스 로직"""

    def __init__(self):
        self.repo = EmergencyCardRepository()

    async def get_my_card(self, user_id: int) -> EmergencyCardResponse:
        """내 응급 카드 조회"""
        card = await self.repo.get_by_user(user_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="응급 카드가 없습니다. 먼저 생성해주세요.",
            )
        return EmergencyCardResponse.model_validate(card)

    async def create_or_update_card(self, user_id: int, data: EmergencyCardCreateRequest) -> EmergencyCardResponse:
        """응급 카드 생성/수정"""
        card = await self.repo.create_or_update(
            user_id=user_id,
            **data.model_dump(),
        )
        return EmergencyCardResponse.model_validate(card)

    async def trigger_sos(self, user_id: int, data: SOSTriggerRequest) -> SOSTriggerResponse:
        """SOS 발송 — 응급 카드 정보 + 위치를 보호자에게 알림 생성"""
        card = await self.repo.get_by_user(user_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="응급 카드가 없습니다. SOS 전송 전 응급 카드를 먼저 등록해주세요.",
            )

        guardians = await Guardian.filter(user_id=user_id, is_active=True).all()

        card_summary = (
            f"혈액형: {card.blood_type or '미입력'} | "
            f"알레르기: {card.allergies or '없음'} | "
            f"만성질환: {card.chronic_conditions or '없음'}"
        )
        location_text = f"위도 {data.latitude:.6f}, 경도 {data.longitude:.6f}"
        content = f"[SOS] {card_summary} | 위치: {location_text}"

        now = datetime.now()
        notified_count = 0
        for guardian in guardians:
            await Notification.create(
                user_id=user_id,
                notification_type=NotificationType.EMERGENCY,
                title=f"[SOS] {guardian.name}님께 응급 알림",
                content=content,
                scheduled_at=now,
                sent_at=now,
            )
            notified_count += 1

        await AuditLog.create(
            user_id=user_id,
            action="EMERGENCY_SOS_TRIGGER",
            detail={
                "latitude": data.latitude,
                "longitude": data.longitude,
                "notified_count": notified_count,
                "blood_type": card.blood_type,
            },
        )

        logger.info(
            "SOS triggered user_id=%s lat=%s lng=%s notified=%s",
            user_id,
            data.latitude,
            data.longitude,
            notified_count,
        )

        return SOSTriggerResponse(
            status="sent",
            notified_count=notified_count,
            latitude=data.latitude,
            longitude=data.longitude,
        )
