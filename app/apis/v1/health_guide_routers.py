from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
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


@health_guide_router.get(
    "/{guide_id}",
    response_model=HealthGuideResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_consent(ConsentType.MEDICAL_DATA))],
)
async def get_guide_detail(
    guide_id: UUID,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthGuideService, Depends(HealthGuideService)],
) -> Response:
    """가이드 상세 조회 (캐시 적용, TTL 30분)"""
    result = await service.get_guide_by_id(guide_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="가이드를 찾을 수 없습니다.")
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)
