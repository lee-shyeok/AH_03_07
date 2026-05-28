from __future__ import annotations

from enum import StrEnum

from tortoise import fields, models


class DiseaseCode(StrEnum):
    RA = "RA"
    SLE = "SLE"


class UserDisease(models.Model):
    """REQ-DISE-001/002 — 자가면역 모드 사용자의 등록 질환."""

    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="diseases", on_delete=fields.CASCADE)
    disease_code = fields.CharEnumField(enum_type=DiseaseCode, max_length=16)
    diagnosed_date = fields.DateField(null=True)
    note = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    deleted_at = fields.DatetimeField(null=True)

    class Meta:
        table = "user_diseases"
