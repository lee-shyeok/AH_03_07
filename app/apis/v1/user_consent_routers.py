from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_request_user
from app.dtos.user_consents import (
    ConsentCreateRequest,
    ConsentListResponse,
    ConsentResponse,
)
from app.models.users import User
from app.services.user_consents import UserConsentService

user_consent_router = APIRouter(prefix="/users/me/consents", tags=["user-consents"])


@user_consent_router.get(
    "",
    response_model=ConsentListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_my_consents(
    user: Annotated[User, Depends(get_request_user)],
    consent_service: Annotated[UserConsentService, Depends(UserConsentService)],
) -> Response:
    """내 동의 이력 조회"""
    result = await consent_service.get_user_consents(user_id=user.id)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@user_consent_router.post(
    "",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_consent(
    request: ConsentCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    consent_service: Annotated[UserConsentService, Depends(UserConsentService)],
) -> Response:
    """동의 추가/갱신 (기존 동의는 자동 철회)"""
    result = await consent_service.create_or_update_consent(user_id=user.id, data=request)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_201_CREATED)
