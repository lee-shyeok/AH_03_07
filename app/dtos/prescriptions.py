from datetime import date, datetime
from uuid import UUID

from app.models.medical_documents import DocumentType, UploadStatus
from pydantic import BaseModel

from app.models.prescriptions import OCRStatus


class MedicalDocumentCreateRequest(BaseModel):
    document_type: DocumentType
    file_s3_url: str
    original_filename: str
    mime_type: str | None = None


class MedicalDocumentResponse(BaseModel):
    id: UUID
    document_type: DocumentType
    file_s3_url: str
    original_filename: str
    mime_type: str | None
    upload_status: UploadStatus
    uploaded_at: datetime

    class Config:
        from_attributes = True


class PrescriptionCreateRequest(BaseModel):
    image_s3_url: str
    document_id: UUID | None = None


class PrescriptionResponse(BaseModel):
    id: UUID
    image_s3_url: str
    ocr_status: OCRStatus
    user_confirmed: bool
    prescription_date: date | None
    hospital_name: str | None
    diagnosis_text: str | None
    created_at: datetime
    updated_at: datetime

    # NOTI-007: 진행률 정보
    end_date: date | None = None
    progress_percentage: int | None = None
    days_remaining: int | None = None
    is_near_end: bool | None = None

    class Config:
        from_attributes = True


class PrescriptionListResponse(BaseModel):
    prescriptions: list[PrescriptionResponse]
    total: int


class PrescriptionConfirmRequest(BaseModel):
    user_confirmed: bool
    prescription_date: date | None = None
    hospital_name: str | None = None
    diagnosis_text: str | None = None
