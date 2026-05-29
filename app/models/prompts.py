import uuid
from enum import StrEnum

from tortoise import fields, models


class PromptType(StrEnum):
    HEALTH_GUIDE = "HEALTH_GUIDE"
    OCR_EXTRACT = "OCR_EXTRACT"
    OCR_STRUCTURE = "OCR_STRUCTURE"
    MEDICATION_INFO = "MEDICATION_INFO"


class Prompt(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    prompt_type = fields.CharEnumField(enum_type=PromptType, max_length=50)
    name = fields.CharField(max_length=200)
    version = fields.CharField(max_length=20, default="v1.0")
    template_text = fields.TextField()
    variables = fields.JSONField(null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "prompts"
        unique_together = (("prompt_type", "version"),)
