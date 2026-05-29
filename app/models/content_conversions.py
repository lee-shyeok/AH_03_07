import uuid
from enum import StrEnum

from tortoise import fields, models


class ConversionType(StrEnum):
    CARD = "CARD"
    TTS = "TTS"


class ConversionStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ContentConversion(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", related_name="conversions", on_delete=fields.CASCADE)
    guide = fields.ForeignKeyField("models.HealthGuide", related_name="conversions", on_delete=fields.CASCADE)
    conversion_type = fields.CharEnumField(enum_type=ConversionType, max_length=20)
    status = fields.CharEnumField(enum_type=ConversionStatus, max_length=20, default=ConversionStatus.PENDING)
    file_url = fields.CharField(max_length=500, null=True)
    file_urls = fields.JSONField(null=True)
    error_message = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    completed_at = fields.DatetimeField(null=True)

    class Meta:
        table = "content_conversions"
