from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.models.health_metrics import HealthMetric, MetricType


class HealthMetricRepository:
    """건강 지표 DB 쿼리"""

    @staticmethod
    async def get_user_metrics(user_id: UUID) -> list[HealthMetric]:
        """사용자의 모든 건강 지표 조회"""
        return await HealthMetric.filter(user_id=user_id).order_by("-measured_at").all()

    @staticmethod
    async def get_user_metrics_by_type(user_id: UUID, metric_type: MetricType) -> list[HealthMetric]:
        """특정 종류의 건강 지표 조회"""
        return (
            await HealthMetric.filter(
                user_id=user_id,
                metric_type=metric_type,
            )
            .order_by("-measured_at")
            .all()
        )

    @staticmethod
    async def create_metric(
        user_id: UUID,
        metric_type: MetricType,
        user_recorded_value: Decimal,
        measured_at: datetime,
        notes: str | None,
        diastolic_value: Decimal | None = None,
    ) -> HealthMetric:
        """건강 지표 생성"""
        return await HealthMetric.create(
            user_id=user_id,
            metric_type=metric_type,
            user_recorded_value=user_recorded_value,
            diastolic_value=diastolic_value,
            measured_at=measured_at,
            notes=notes,
        )
