import uuid
from enum import StrEnum

from tortoise import fields, models


class NotificationType(StrEnum):
    MEDICATION = "MEDICATION"
    DIARY = "DIARY"
    HEALTH_METRIC = "HEALTH_METRIC"
    EMERGENCY = "EMERGENCY"
    GUIDE = "GUIDE"


class Notification(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", related_name="notifications", on_delete=fields.CASCADE)
    notification_type = fields.CharEnumField(enum_type=NotificationType, max_length=30)
    title = fields.CharField(max_length=200)
    content = fields.TextField()
    is_read = fields.BooleanField(default=False)
    scheduled_at = fields.DatetimeField()
    sent_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "notifications"
