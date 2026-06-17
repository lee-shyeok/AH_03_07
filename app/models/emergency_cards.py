import uuid
from enum import StrEnum

from tortoise import fields, models


class SirenMode(StrEnum):
    NORMAL = "NORMAL"
    SILENT = "SILENT"
    OFF = "OFF"


class EmergencyCard(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.OneToOneField("models.User", related_name="emergency_card", on_delete=fields.CASCADE)
    blood_type = fields.CharField(max_length=10, null=True)
    allergies = fields.TextField(null=True)
    chronic_conditions = fields.TextField(null=True)
    medications = fields.TextField(null=True)
    emergency_contacts = fields.JSONField(null=True)
    siren_mode = fields.CharEnumField(enum_type=SirenMode, max_length=20, default=SirenMode.NORMAL)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "emergency_cards"
