from __future__ import annotations

from enum import StrEnum

from tortoise import fields, models


class LupusSkinSymptomType(StrEnum):
    RASH = "RASH"
    ORAL_ULCER = "ORAL_ULCER"
    HAIR_LOSS = "HAIR_LOSS"


class LupusSkinLog(models.Model):
    """REQ-LUPUS-001 — SLE 특이 피부 증상 기록 (순수 저장, 해석 없음)."""

    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="lupus_skin_logs", on_delete=fields.CASCADE)
    symptom_type = fields.CharEnumField(enum_type=LupusSkinSymptomType, max_length=16)
    log_date = fields.DateField()
    note = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    deleted_at = fields.DatetimeField(null=True)

    class Meta:
        table = "lupus_skin_logs"
