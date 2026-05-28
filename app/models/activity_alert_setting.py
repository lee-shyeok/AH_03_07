from __future__ import annotations

from enum import StrEnum

from tortoise import fields, models


class AlertCriterion(StrEnum):
    PAIN = "PAIN"
    MORNING_STIFFNESS = "MORNING_STIFFNESS"
    FATIGUE = "FATIGUE"


class ActivityAlertSetting(models.Model):
    """REQ-ACTV-003 — 사용자가 직접 설정한 활성도 자가 모니터링 알림 기준 (사용자당 1개)."""

    id = fields.BigIntField(primary_key=True)
    user = fields.OneToOneField("models.User", related_name="activity_alert_setting", on_delete=fields.CASCADE)
    pain_threshold = fields.IntField(null=True)
    pain_consecutive_days = fields.IntField(null=True)
    morning_stiffness_threshold = fields.IntField(null=True)
    fatigue_threshold = fields.IntField(null=True)
    alert_message = fields.TextField()
    is_enabled = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "activity_alert_settings"
