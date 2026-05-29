from fastapi import HTTPException, status

from app.dtos.emergency_cards import EmergencyCardCreateRequest, EmergencyCardResponse
from app.repositories.emergency_card_repository import EmergencyCardRepository


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
