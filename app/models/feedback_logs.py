import uuid
from enum import StrEnum

from tortoise import fields, models


class TargetType(StrEnum):
    GUIDE = "GUIDE"
    CHAT = "CHAT"
    OCR = "OCR"
    PILL = "PILL"


class FeedbackType(StrEnum):
    RATING = "RATING"
    THUMBS_UP = "THUMBS_UP"
    THUMBS_DOWN = "THUMBS_DOWN"
    REGENERATE = "REGENERATE"


class FeedbackLog(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", related_name="feedbacks", on_delete=fields.CASCADE)
    target_type = fields.CharEnumField(enum_type=TargetType, max_length=20)
    target_id = fields.UUIDField()
    feedback_type = fields.CharEnumField(enum_type=FeedbackType, max_length=20)
    rating = fields.IntField(null=True)
    comment = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "feedback_logs"
