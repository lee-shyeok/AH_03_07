from __future__ import annotations

from enum import StrEnum

from tortoise import fields, models


class RiskFlagSourceType(StrEnum):
    SYMPTOM_CHECK = "SYMPTOM_CHECK"
    RISK_PROFILE = "RISK_PROFILE"
    LAB_RESULT = "LAB_RESULT"


class RiskFlagStatus(StrEnum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class RiskFlag(models.Model):
    """REQ-AUTO-006 — 고위험 플래그 저장소. 게이트 엔진 매칭 결과를 DB에 영속."""

    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="risk_flags", on_delete=fields.CASCADE)
    source_type = fields.CharEnumField(enum_type=RiskFlagSourceType, max_length=16)
    source_id = fields.BigIntField(null=True)
    flag_code = fields.CharField(max_length=64)
    flag_label = fields.CharField(max_length=128)
    category = fields.CharField(max_length=32)
    message = fields.TextField()
    red_flag = fields.BooleanField(default=False)
    consultation_recommended = fields.BooleanField(default=True)
    status = fields.CharEnumField(enum_type=RiskFlagStatus, default=RiskFlagStatus.ACTIVE, max_length=16)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "risk_flags"
