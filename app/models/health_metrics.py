import uuid
from enum import StrEnum

from tortoise import fields, models


class MetricType(StrEnum):
    BLOOD_PRESSURE = "BLOOD_PRESSURE"
    BLOOD_SUGAR = "BLOOD_SUGAR"
    WEIGHT = "WEIGHT"
    HEART_RATE = "HEART_RATE"


class HealthMetric(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", related_name="health_metrics", on_delete=fields.CASCADE)
    metric_type = fields.CharEnumField(enum_type=MetricType, max_length=30)
    user_recorded_value = fields.DecimalField(max_digits=10, decimal_places=2)
    diastolic_value = fields.DecimalField(max_digits=10, decimal_places=2, null=True)
    measured_at = fields.DatetimeField()
    notes = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "health_metrics"
