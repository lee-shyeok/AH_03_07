import uuid
from enum import StrEnum

from tortoise import fields, models


class ShareDuration(StrEnum):
    ONE_DAY = "ONE_DAY"
    ONE_WEEK = "ONE_WEEK"
    ONE_MONTH = "ONE_MONTH"
    UNTIL_REVOKED = "UNTIL_REVOKED"


class ShareLink(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", related_name="share_links", on_delete=fields.CASCADE)
    guardian = fields.ForeignKeyField("models.Guardian", related_name="share_links", on_delete=fields.CASCADE)
    token = fields.CharField(max_length=100, unique=True)
    duration = fields.CharEnumField(enum_type=ShareDuration, max_length=30)
    categories = fields.JSONField()
    include_summary_only = fields.BooleanField(default=True)
    expires_at = fields.DatetimeField()
    is_revoked = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "share_links"
