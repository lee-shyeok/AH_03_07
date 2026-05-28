import uuid
from enum import StrEnum

from tortoise import fields, models


class ConsentType(StrEnum):
    TERMS_OF_SERVICE = "TERMS_OF_SERVICE"
    PRIVACY_POLICY = "PRIVACY_POLICY"
    MEDICAL_DATA = "MEDICAL_DATA"
    MARKETING = "MARKETING"


class UserConsent(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", related_name="consents", on_delete=fields.CASCADE)
    consent_type = fields.CharEnumField(enum_type=ConsentType, max_length=50)
    agreed = fields.BooleanField()
    version = fields.CharField(max_length=20)
    agreed_at = fields.DatetimeField(auto_now_add=True)
    withdrawn_at = fields.DatetimeField(null=True)

    class Meta:
        table = "user_consents"
