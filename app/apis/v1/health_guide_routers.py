from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.consent import require_consent
from app.dependencies.security import get_request_user
from app.dtos.health_guides import (
    HealthGuideCreateRequest,
    HealthGuideListResponse,
    HealthGuideResponse,
)
from app.models.user_consents import ConsentType
from app.models.users import User
from app.services.health_guides import HealthGuideService

health_guide_router = APIRouter(prefix="/health-guides", tags=["health-guides"])


@health_guide_router.get(
    "",
    response_model=HealthGuideListResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_consent(ConsentType.MEDICAL_DATA))],
)
async def get_my_guides(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthGuideService, Depends(HealthGuideService)],
) -> Response:
    """내 가이드 목록"""
    result = await service.get_my_guides(user_id=user.id)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@health_guide_router.post(
    "",
    response_model=HealthGuideResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_consent(ConsentType.MEDICAL_DATA))],
)
async def generate_guide(
    request: HealthGuideCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthGuideService, Depends(HealthGuideService)],
) -> Response:
    """AI 가이드 생성!"""
    result = await service.generate_guide(user_id=user.id, data=request)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_201_CREATED)
