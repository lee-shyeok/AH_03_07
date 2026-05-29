from uuid import UUID

from app.models.emergency_cards import EmergencyCard


class EmergencyCardRepository:
    """응급 카드 DB 쿼리"""

    @staticmethod
    async def get_by_user(user_id: UUID) -> EmergencyCard | None:
        """사용자의 응급 카드 조회"""
        return await EmergencyCard.filter(user_id=user_id).first()

    @staticmethod
    async def create_or_update(user_id: UUID, **kwargs) -> EmergencyCard:
        """응급 카드 생성 또는 수정 (있으면 수정, 없으면 생성)"""
        card = await EmergencyCard.filter(user_id=user_id).first()
        if card:
            for key, value in kwargs.items():
                setattr(card, key, value)
            await card.save()
            return card
        return await EmergencyCard.create(user_id=user_id, **kwargs)
