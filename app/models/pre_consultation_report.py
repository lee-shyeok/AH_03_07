from __future__ import annotations

from enum import StrEnum

from tortoise import fields, models


class ReportStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PreConsultationReport(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField(
        "models.User",
        on_delete=fields.CASCADE,
        related_name="pre_consultation_reports",
    )
    status = fields.CharEnumField(ReportStatus, max_length=20, default=ReportStatus.PENDING)
    visit_date = fields.DateField()
    period_days = fields.IntField(default=90)
    pdf = fields.BinaryField(null=True)
    error_message = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "pre_consultation_reports"
