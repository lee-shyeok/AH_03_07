from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.consent import require_consent
from app.dependencies.security import get_request_user
from app.dtos.health_metrics import (
    HealthMetricCreateRequest,
    HealthMetricListResponse,
    HealthMetricResponse,
)
from app.models.user_consents import ConsentType
from app.models.users import User
from app.services.health_metrics import HealthMetricService

health_metric_router = APIRouter(prefix="/health-metrics", tags=["health-metrics"])


@health_metric_router.get(
    "",
    response_model=HealthMetricListResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_consent(ConsentType.MEDICAL_DATA))],
)
async def get_my_health_metrics(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthMetricService, Depends(HealthMetricService)],
) -> Response:
    """내 건강 지표 조회"""
    result = await service.get_user_metrics(user_id=user.id)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)


@health_metric_router.post(
    "",
    response_model=HealthMetricResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_consent(ConsentType.MEDICAL_DATA))],
)
async def create_health_metric(
    request: HealthMetricCreateRequest,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthMetricService, Depends(HealthMetricService)],
) -> Response:
    """건강 지표 생성"""
    result = await service.create_metric(user_id=user.id, data=request)
    return Response(result.model_dump(mode="json"), status_code=status.HTTP_201_CREATED)
