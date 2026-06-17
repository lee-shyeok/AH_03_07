import uuid
from enum import StrEnum

from tortoise import fields, models


class OverallCondition(StrEnum):
    VERY_BAD = "VERY_BAD"
    BAD = "BAD"
    NORMAL = "NORMAL"
    GOOD = "GOOD"
    VERY_GOOD = "VERY_GOOD"


class DiarySymptomLog(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", related_name="symptom_logs", on_delete=fields.CASCADE)
    log_date = fields.DateField()
    overall_condition = fields.CharEnumField(enum_type=OverallCondition, max_length=20)
    body_parts = fields.JSONField(null=True)
    feeling = fields.JSONField(null=True)
    medications = fields.JSONField(null=True)
    memo = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "diary_symptom_logs"
