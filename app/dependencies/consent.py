from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.dependencies.security import get_request_user
from app.models.user_consents import ConsentType
from app.models.users import User
from app.services.user_consents import UserConsentService


def require_consent(consent_type: ConsentType) -> Callable:
    """동의 체크 의존성 함수

    팀원 사용법:
        @router.post(
            "/your-endpoint",
            dependencies=[Depends(require_consent(ConsentType.MEDICAL_DATA))]
        )
        async def your_api(...):
            ...
    """

    async def dependency(
        user: Annotated[User, Depends(get_request_user)],
        consent_service: Annotated[UserConsentService, Depends(UserConsentService)],
    ) -> User:
        is_active = await consent_service.is_consent_active(
            user_id=user.id,
            consent_type=consent_type,
        )
        if not is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": "CONSENT_REQUIRED",
                    "message": f"{consent_type.value} 동의가 필요합니다.",
                    "consent_type": consent_type.value,
                },
            )
        return user

    return dependency
