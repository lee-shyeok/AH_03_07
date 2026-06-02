from __future__ import annotations

from enum import StrEnum

from tortoise import fields, models


class GuideGenerationJobStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class GuideGenerationJob(models.Model):
    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField(
        "models.User",
        on_delete=fields.CASCADE,
        related_name="guide_generation_jobs",
    )
    status = fields.CharEnumField(
        GuideGenerationJobStatus,
        max_length=20,
        default=GuideGenerationJobStatus.PENDING,
    )
    guide = fields.ForeignKeyField(
        "models.AutoGuide",
        null=True,
        on_delete=fields.SET_NULL,
        related_name="generation_jobs",
    )
    trigger_type = fields.CharField(max_length=20)
    blocked_reason = fields.CharField(max_length=40, null=True)
    trigger_emergency_modal = fields.BooleanField(default=False)
    error_message = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "guide_generation_jobs"
