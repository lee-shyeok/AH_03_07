from __future__ import annotations

from tortoise import fields, models


class DiseaseActivityLog(models.Model):
    """REQ-ACTV-001 — 자가면역질환 공통 활성도 정량 일일 기록 (사용자·일자당 1건)."""

    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="activity_logs", on_delete=fields.CASCADE)
    log_date = fields.DateField()
    pain_vas = fields.IntField()
    fatigue = fields.IntField()
    morning_stiffness_min = fields.IntField(null=True)
    joint_swelling_areas = fields.JSONField(null=True)
    daily_difficulty = fields.IntField()
    note = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "disease_activity_logs"
        unique_together = (("user", "log_date"),)
