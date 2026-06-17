from decimal import Decimal

from app.dtos.health_metrics import (
    HealthMetricCreateRequest,
    HealthMetricListResponse,
    HealthMetricResponse,
)
from app.repositories.health_metric_repository import HealthMetricRepository


class HealthMetricService:
    """건강 지표 비즈니스 로직"""

    def __init__(self):
        self.repo = HealthMetricRepository()

    async def get_user_metrics(self, user_id: int) -> HealthMetricListResponse:
        """사용자 건강 지표 전체 조회"""
        metrics = await self.repo.get_user_metrics(user_id)
        return HealthMetricListResponse(
            metrics=[HealthMetricResponse.model_validate(m) for m in metrics],
            total=len(metrics),
        )

    async def create_metric(self, user_id: int, data: HealthMetricCreateRequest) -> HealthMetricResponse:
        """건강 지표 생성"""
        new_metric = await self.repo.create_metric(
            user_id=user_id,
            metric_type=data.metric_type,
            user_recorded_value=data.user_recorded_value,
            diastolic_value=Decimal(data.diastolic_value) if data.diastolic_value is not None else None,
            measured_at=data.measured_at,
            notes=data.notes,
        )
        return HealthMetricResponse.model_validate(new_metric)
