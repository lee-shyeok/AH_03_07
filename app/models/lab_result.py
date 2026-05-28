from __future__ import annotations

from tortoise import fields, models


class LabResult(models.Model):
    """REQ-LAB-001 — 사용자가 직접 입력한 검사 결과 (수동 입력·보관)."""

    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="lab_results", on_delete=fields.CASCADE)
    test_date = fields.DateField()
    test_item = fields.CharField(max_length=128)
    value = fields.CharField(max_length=64)
    reference_range = fields.CharField(max_length=64, null=True)
    note = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    deleted_at = fields.DatetimeField(null=True)

    class Meta:
        table = "lab_results"
