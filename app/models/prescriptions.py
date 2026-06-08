import uuid
from enum import StrEnum

from tortoise import fields, models


class OCRStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Prescription(models.Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user = fields.ForeignKeyField("models.User", related_name="prescriptions", on_delete=fields.CASCADE)
    document = fields.ForeignKeyField(
        "models.MedicalDocument", related_name="prescriptions", null=True, on_delete=fields.SET_NULL
    )
    image_s3_url = fields.TextField()
    ocr_raw_text = fields.TextField(null=True)
    ocr_status = fields.CharEnumField(enum_type=OCRStatus, max_length=20, default=OCRStatus.PENDING)
    user_confirmed = fields.BooleanField(default=False)
    prescription_date = fields.DateField(null=True)
    hospital_name = fields.CharField(max_length=100, null=True)
    diagnosis_text = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "prescriptions"
