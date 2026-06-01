from __future__ import annotations

from enum import StrEnum

from tortoise import fields, models


class AutoimmunePregnancyStatus(StrEnum):
    NONE = "none"
    PREGNANT = "pregnant"
    BREASTFEEDING = "breastfeeding"
    PLANNING = "planning"


class AutoimmuneProfile(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.OneToOneField("models.User", related_name="autoimmune_profile", on_delete=fields.CASCADE)
    risk_factors = fields.JSONField(default=dict)
    pregnancy_status = fields.CharEnumField(
        enum_type=AutoimmunePregnancyStatus,
        default=AutoimmunePregnancyStatus.NONE,
        max_length=16,
    )
    vaccination_history = fields.JSONField(default=list)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "autoimmune_profiles"
