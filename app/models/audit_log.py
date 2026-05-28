from __future__ import annotations

from tortoise import fields, models


class AuditLog(models.Model):
    """NFR-COMPLI-004 — 민감정보 처리 감사 로그 (append-only)."""

    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="audit_logs", on_delete=fields.CASCADE)
    action = fields.CharField(max_length=64)
    detail = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "audit_logs"
