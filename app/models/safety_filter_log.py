"""NFR-SAFE-003 — 안전 표현 필터 차단 이력 모델."""

from __future__ import annotations

import uuid

from tortoise import fields, models


class SafetyFilterLog(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user_id = fields.BigIntField(null=True)
    target_type = fields.CharField(max_length=50)
    target_id = fields.CharField(max_length=100, null=True)
    blocked_reason = fields.CharField(max_length=100)
    original_text = fields.TextField()
    safe_replacement_text = fields.TextField()
    filter_stage = fields.CharField(max_length=30)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "safety_filter_logs"
