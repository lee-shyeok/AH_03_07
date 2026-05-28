from enum import StrEnum

from tortoise import fields, models


class DocumentType(StrEnum):
    PRESCRIPTION = "prescription"
    MEDICAL_RECORD = "medical_record"
    PILL_BAG = "pill_bag"
    LAB_RESULT = "lab_result"
    HEALTH_CHECKUP = "health_checkup"
    OTHER = "other"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OcrJobStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MedicalDocument(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField("models.User", related_name="medical_documents")
    document_type = fields.CharEnumField(enum_type=DocumentType, max_length=32)
    file_url = fields.CharField(max_length=512)
    original_filename = fields.CharField(max_length=255)
    upload_status = fields.CharEnumField(enum_type=DocumentStatus, default=DocumentStatus.UPLOADED, max_length=32)
    user_confirmed = fields.BooleanField(default=False)
    confirmed_at = fields.DatetimeField(null=True)
    structured_data = fields.JSONField(null=True)
    is_deleted = fields.BooleanField(default=False)
    deleted_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "medical_documents"


class OcrJob(models.Model):
    id = fields.UUIDField(primary_key=True)
    document = fields.ForeignKeyField("models.MedicalDocument", related_name="ocr_jobs")
    status = fields.CharEnumField(enum_type=OcrJobStatus, default=OcrJobStatus.PENDING, max_length=32)
    structured_data = fields.JSONField(null=True)
    confidence_score = fields.FloatField(null=True)
    error_message = fields.CharField(max_length=512, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "ocr_jobs"