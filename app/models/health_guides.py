import uuid
from enum import StrEnum

from tortoise import fields, models


class GuideType(StrEnum):
    EXERCISE = "EXERCISE"
    DIET = "DIET"
    LIFESTYLE = "LIFESTYLE"
    MEDICATION = "MEDICATION"
    GENERAL = "GENERAL"


class GuideStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class HealthGuide(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", related_name="health_guides", on_delete=fields.CASCADE)
    guide_type = fields.CharEnumField(enum_type=GuideType, max_length=50)
    status = fields.CharEnumField(enum_type=GuideStatus, max_length=30, default=GuideStatus.PENDING)
    user_question = fields.TextField()
    guide_content = fields.TextField(null=True)
    prompt_used_id = fields.UUIDField(null=True)
    metadata = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "health_guides"
