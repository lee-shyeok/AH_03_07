from __future__ import annotations

from enum import StrEnum

from tortoise import fields, models


class AutoGuideStatus(StrEnum):
    GENERATED = "GENERATED"
    BLOCKED_HIGH_RISK = "BLOCKED_HIGH_RISK"
    GENERATION_FAILED = "GENERATION_FAILED"


class AutoGuide(models.Model):
    """REQ-AUTO-005 — 자가면역 맞춤 안내문 생성 결과 영속화."""

    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="auto_guides", on_delete=fields.CASCADE)
    status = fields.CharEnumField(enum_type=AutoGuideStatus, max_length=24)
    medication_general = fields.TextField()
    side_effect_monitoring = fields.JSONField()
    lifestyle_info = fields.TextField()
    symptom_summary = fields.TextField()
    sources = fields.JSONField()
    disclaimer = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "auto_guides"
