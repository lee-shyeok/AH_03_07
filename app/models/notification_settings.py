import uuid

from tortoise import fields, models


class NotificationSetting(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.OneToOneField("models.User", related_name="notification_setting", on_delete=fields.CASCADE)
    medication_enabled = fields.BooleanField(default=True)
    diary_enabled = fields.BooleanField(default=True)
    health_metric_enabled = fields.BooleanField(default=True)
    emergency_enabled = fields.BooleanField(default=True)
    quiet_hours_start = fields.TimeField(null=True)
    quiet_hours_end = fields.TimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "notification_settings"
