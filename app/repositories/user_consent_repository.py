from datetime import datetime
from uuid import UUID

from app.models.user_consents import ConsentType, UserConsent


class UserConsentRepository:
    """동의 정보 DB 쿼리 담당"""

    @staticmethod
    async def get_user_consents(user_id: UUID) -> list[UserConsent]:
        """사용자의 모든 동의 이력 조회"""
        return await UserConsent.filter(user_id=user_id).order_by("-agreed_at").all()

    @staticmethod
    async def get_active_consent(user_id: UUID, consent_type: ConsentType) -> UserConsent | None:
        """유효한 동의 한 건 조회 (철회 안 된 것)"""
        return await UserConsent.filter(
            user_id=user_id,
            consent_type=consent_type,
            agreed=True,
            withdrawn_at=None,
        ).first()

    @staticmethod
    async def get_active_consents_by_type(user_id: UUID, consent_type: ConsentType) -> list[UserConsent]:
        """특정 종류의 활성 동의 목록 (철회용)"""
        return await UserConsent.filter(
            user_id=user_id,
            consent_type=consent_type,
            withdrawn_at=None,
        ).all()

    @staticmethod
    async def create_consent(user_id: UUID, consent_type: ConsentType, agreed: bool, version: str) -> UserConsent:
        """새 동의 생성"""
        return await UserConsent.create(
            user_id=user_id,
            consent_type=consent_type,
            agreed=agreed,
            version=version,
        )

    @staticmethod
    async def withdraw_consent(consent: UserConsent) -> UserConsent:
        """동의 철회 (withdrawn_at 설정)"""
        consent.withdrawn_at = datetime.now()
        await consent.save()
        return consent
