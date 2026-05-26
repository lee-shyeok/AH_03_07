import uuid
from enum import StrEnum
from tortoise import fields, models

class AuditAction(StrEnum):
    MODE_CHANGE = "MODE_CHANGE"

class AuditLog(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", related_name="audit_logs", on_delete=fields.CASCADE)
    action = fields.CharEnumField(enum_type=AuditAction, max_length=30)
    before_value = fields.CharField(max_length=100, null=True)
    after_value = fields.CharField(max_length=100, null=True)
    note = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "audit_logs"