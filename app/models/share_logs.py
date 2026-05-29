import uuid

from tortoise import fields, models


class ShareLog(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    share_link = fields.ForeignKeyField("models.ShareLink", related_name="logs", on_delete=fields.CASCADE)
    viewed_at = fields.DatetimeField(auto_now_add=True)
    viewer_ip = fields.CharField(max_length=50, null=True)

    class Meta:
        table = "share_logs"
