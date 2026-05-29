import uuid

from tortoise import fields, models


class Guardian(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", related_name="guardians", on_delete=fields.CASCADE)
    name = fields.CharField(max_length=100)
    phone_number = fields.CharField(max_length=20, null=True)
    email = fields.CharField(max_length=100, null=True)
    relationship = fields.CharField(max_length=50, null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "guardians"
