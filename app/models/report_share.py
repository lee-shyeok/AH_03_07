from __future__ import annotations

from tortoise import fields, models


class ReportShare(models.Model):
    id = fields.BigIntField(primary_key=True)
    report = fields.ForeignKeyField(
        "models.PreConsultationReport",
        on_delete=fields.CASCADE,
        related_name="shares",
    )
    user = fields.ForeignKeyField(
        "models.User",
        on_delete=fields.CASCADE,
        related_name="report_shares",
    )
    recipient_email = fields.CharField(max_length=255)
    token = fields.CharField(max_length=100, unique=True)
    expires_at = fields.DatetimeField()
    is_revoked = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "report_shares"
