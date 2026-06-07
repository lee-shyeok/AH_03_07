from __future__ import annotations

from enum import StrEnum

from tortoise import fields, models


class StressLevel(StrEnum):
    LOW = "LOW"
    MID = "MID"
    HIGH = "HIGH"


class LupusDailyContext(models.Model):
    """REQ-LUPUS-001 — SLE 환자 생활 맥락 일일 기록 (순수 저장, 해석·판정 없음). 사용자·일자당 1건."""

    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="lupus_daily_contexts", on_delete=fields.CASCADE)
    log_date = fields.DateField()
    uv_exposure_minutes = fields.IntField(null=True)
    sleep_hours = fields.FloatField(null=True)
    stress_level = fields.CharEnumField(enum_type=StressLevel, max_length=8, null=True)
    med_taken = fields.BooleanField(null=True)
    note = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "lupus_daily_contexts"
        unique_together = (("user", "log_date"),)
