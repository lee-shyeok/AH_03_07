from enum import StrEnum

from tortoise import fields, models


class DocumentType(StrEnum):
    prescription = "prescription"
    medical_record = "medical_record"
    pill_bag = "pill_bag"
    lab_result = "lab_result"
    health_checkup = "health_checkup"
    other = "other"


class UploadStatus(StrEnum):
    uploaded = "uploaded"
    confirmed = "confirmed"
    deleted = "deleted"


class OcrJobStatus(StrEnum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class MedicalDocument(models.Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="medical_documents", on_delete=fields.CASCADE)
    document_type = fields.CharEnumField(enum_type=DocumentType, max_length=20)
    # [보안] 실제 저장 경로는 서버 내부 전용 — 응답에 절대 노출하지 않음
    file_path = fields.CharField(max_length=500)
    # [보안] 원본 파일명은 표시용으로만 사용 (경로/URL 생성에 사용 금지)
    original_filename = fields.CharField(max_length=255)
    # [보안] UUID 기반 내부 파일명 — 파일 다운로드 토큰으로만 사용
    stored_filename = fields.CharField(max_length=100)
    file_size = fields.IntField(null=True)
    mime_type = fields.CharField(max_length=100, null=True)
    upload_status = fields.CharEnumField(enum_type=UploadStatus, max_length=20, default=UploadStatus.uploaded)
    is_user_confirmed = fields.BooleanField(default=False)
    confirmed_data = fields.TextField(null=True)  # JSON
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    deleted_at = fields.DatetimeField(null=True)

    class Meta:
        table = "medical_documents"


class OcrJob(models.Model):
    id = fields.IntField(pk=True)
    document = fields.ForeignKeyField("models.MedicalDocument", related_name="ocr_jobs", on_delete=fields.CASCADE)
    user = fields.ForeignKeyField("models.User", related_name="ocr_jobs", on_delete=fields.CASCADE)
    status = fields.CharEnumField(enum_type=OcrJobStatus, max_length=20, default=OcrJobStatus.pending)
    raw_text = fields.TextField(null=True)
    structured_data = fields.TextField(null=True)  # JSON
    confidence_score = fields.FloatField(null=True)
    field_confidences = fields.TextField(null=True)  # JSON
    error_message = fields.CharField(max_length=500, null=True)
    started_at = fields.DatetimeField(null=True)
    completed_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "ocr_jobs"
