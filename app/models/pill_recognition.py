from __future__ import annotations

from tortoise import fields, models


class PillRecognition(models.Model):
    """REQ-PILL-001 / REQ-PILL-004 — 약품 이미지 인식 이력."""

    id = fields.BigIntField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="pill_recognitions", on_delete=fields.CASCADE)
    image_url = fields.CharField(max_length=512)
    original_filename = fields.CharField(max_length=255)
    candidates = fields.JSONField(null=True)  # [{ drug_name, confidence }, ...]
    selected_drug_name = fields.CharField(max_length=128, null=True)
    user_confirmed = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "pill_recognitions"
