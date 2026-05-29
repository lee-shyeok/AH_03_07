import uuid

from tortoise import fields, models


class Pharmacy(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    name = fields.CharField(max_length=200)
    address = fields.CharField(max_length=500)
    phone = fields.CharField(max_length=20, null=True)
    latitude = fields.DecimalField(max_digits=10, decimal_places=7)
    longitude = fields.DecimalField(max_digits=10, decimal_places=7)
    operating_hours = fields.JSONField(null=True)
    is_24h_available = fields.BooleanField(default=False)
    is_holiday_available = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "pharmacies"
