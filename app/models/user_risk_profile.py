from __future__ import annotations

from enum import StrEnum

from tortoise import fields, models


class PregnancyStatus(StrEnum):
    NONE = "NONE"
    PREGNANT = "PREGNANT"
    BREASTFEEDING = "BREASTFEEDING"
    PLANNING = "PLANNING"


class UserRiskProfile(models.Model):
    """REQ-AUTO-001 — 자가면역 안내문 생성용 위험요인 프로필 (사용자당 1개)."""

    id = fields.BigIntField(primary_key=True)
    user = fields.OneToOneField("models.User", related_name="risk_profile", on_delete=fields.CASCADE)
    pregnancy_status = fields.CharEnumField(enum_type=PregnancyStatus, default=PregnancyStatus.NONE, max_length=16)
    renal_impairment = fields.BooleanField(default=False)
    hepatic_impairment = fields.BooleanField(default=False)
    infection_history = fields.TextField(null=True)
    drug_allergy = fields.TextField(null=True)
    comorbidities = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_risk_profiles"
