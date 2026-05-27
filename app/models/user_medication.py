from __future__ import annotations

from enum import StrEnum

from tortoise import fields, models


class DrugClass(StrEnum):
    STEROID = "STEROID"
    IMMUNOSUPPRESSANT = "IMMUNOSUPPRESSANT"
    ANTIMALARIAL = "ANTIMALARIAL"
    BIOLOGIC = "BIOLOGIC"
    NSAID = "NSAID"


class UserMedication(models.Model):
    """REQ-AUTO-002 — 사용자가 등록한 자가면역 관련 약물."""

    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="medications", on_delete=fields.CASCADE)
    name = fields.CharField(max_length=128)
    drug_class = fields.CharEnumField(enum_type=DrugClass, max_length=24)
    is_injection = fields.BooleanField(default=False)
    note = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    deleted_at = fields.DatetimeField(null=True)

    class Meta:
        table = "user_medications"
