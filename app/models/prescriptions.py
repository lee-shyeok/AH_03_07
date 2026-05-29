import uuid

from tortoise import fields, models


class Prescription(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", related_name="prescriptions", on_delete=fields.CASCADE)
    ocr_raw_text = fields.TextField(null=True)
    image_url = fields.CharField(max_length=500, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "prescriptions"
