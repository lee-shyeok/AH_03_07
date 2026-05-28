from tortoise.transactions import in_transaction

from app.dtos.user_consents import ConsentCreateRequest, ConsentListResponse, ConsentResponse
from app.models.user_consents import ConsentType
from app.repositories.user_consent_repository import UserConsentRepository


class UserConsentService:
    """동의 처리 비즈니스 로직"""

    def __init__(self):
        self.repo = UserConsentRepository()

    async def get_user_consents(self, user_id: int) -> ConsentListResponse:
        """사용자 동의 이력 조회"""
        consents = await self.repo.get_user_consents(user_id)
        return ConsentListResponse(
            consents=[ConsentResponse.model_validate(c) for c in consents],
            total=len(consents),
        )

    async def create_or_update_consent(self, user_id: int, data: ConsentCreateRequest) -> ConsentResponse:
        """동의 추가/갱신 (기존 활성 동의는 자동 철회)"""
        async with in_transaction():
            # 1. 기존 활성 동의 철회
            existing_consents = await self.repo.get_active_consents_by_type(
                user_id=user_id,
                consent_type=data.consent_type,
            )
            for old_consent in existing_consents:
                await self.repo.withdraw_consent(old_consent)

            # 2. 새 동의 생성
            new_consent = await self.repo.create_consent(
                user_id=user_id,
                consent_type=data.consent_type,
                agreed=data.agreed,
                version=data.version,
            )

        return ConsentResponse.model_validate(new_consent)

    async def is_consent_active(self, user_id: int, consent_type: ConsentType) -> bool:
        """동의 유효 여부 확인 (require_consent에서 사용)"""
        consent = await self.repo.get_active_consent(user_id=user_id, consent_type=consent_type)
        return consent is not None
