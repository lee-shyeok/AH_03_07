import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator

from ocr_models import DocumentTypeEnum, OcrJobStatusEnum, UploadStatusEnum

# ── 업로드 응답 ───────────────────────────────────────────
# [수정 #10] 모델 PK는 id → 응답 필드도 id로 통일 (document_id 제거)

class MedicalDocumentUploadResponse(BaseModel):
    id: int
    document_type: DocumentTypeEnum
    upload_status: UploadStatusEnum
    original_filename: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── 목록 조회 ─────────────────────────────────────────────

class MedicalDocumentBrief(BaseModel):
    id: int
    document_type: DocumentTypeEnum
    original_filename: str
    upload_status: UploadStatusEnum
    is_user_confirmed: bool
    file_size: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class MedicalDocumentListResponse(BaseModel):
    items: list[MedicalDocumentBrief]
    total: int
    page: int
    size: int


# ── 상세 조회 ─────────────────────────────────────────────
# [수정 #2] file_url을 original_filename 기반으로 만들지 않음
#           → /v1/medical-documents/{id}/download 엔드포인트 경유 방식으로 변경
#           → 직접 경로 노출 없이 인증 후 다운로드 가능

class MedicalDocumentDetail(BaseModel):
    id: int
    document_type: DocumentTypeEnum
    original_filename: str
    download_url: str          # 인증 필요한 다운로드 엔드포인트 URL
    upload_status: UploadStatusEnum
    is_user_confirmed: bool
    confirmed_data: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_url(cls, doc, base_url: str) -> "MedicalDocumentDetail":
        confirmed = None
        if doc.confirmed_data:
            try:
                confirmed = json.loads(doc.confirmed_data)
            except (json.JSONDecodeError, ValueError):
                confirmed = None

        return cls(
            id=doc.id,
            document_type=doc.document_type,
            original_filename=doc.original_filename,
            # [수정 #2] 파일명/경로 대신 ID 기반 다운로드 URL 사용
            download_url=f"{base_url}/v1/medical-documents/{doc.id}/download",
            upload_status=doc.upload_status,
            is_user_confirmed=doc.is_user_confirmed,
            confirmed_data=confirmed,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )


# ── OCR 작업 응답 ──────────────────────────────────────────

class OcrJobCreateResponse(BaseModel):
    job_id: int
    document_id: int
    status: OcrJobStatusEnum

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, job) -> "OcrJobCreateResponse":
        return cls(job_id=job.id, document_id=job.document_id, status=job.status)


class FieldConfidence(BaseModel):
    value: str | None = None
    confidence: float        # 0.0 ~ 1.0
    low_confidence: bool     # True면 프론트에서 노란색 하이라이트


class OcrJobResult(BaseModel):
    job_id: int
    document_id: int
    status: OcrJobStatusEnum
    structured_data: dict[str, Any] | None = None
    field_confidences: dict[str, FieldConfidence] | None = None
    confidence_score: float | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    @classmethod
    def from_orm(cls, job) -> "OcrJobResult":
        structured = None
        if job.structured_data:
            try:
                structured = json.loads(job.structured_data)
            except (json.JSONDecodeError, ValueError):
                structured = None

        field_conf = None
        if job.field_confidences:
            try:
                raw = json.loads(job.field_confidences)
                field_conf = {k: FieldConfidence(**v) for k, v in raw.items()}
            except (json.JSONDecodeError, ValueError, TypeError):
                field_conf = None

        return cls(
            job_id=job.id,
            document_id=job.document_id,
            status=job.status,
            structured_data=structured,
            field_confidences=field_conf,
            confidence_score=job.confidence_score,
            error_message=job.error_message,
            created_at=job.created_at,
            completed_at=job.completed_at,
        )


# ── OCR 결과 확정 ─────────────────────────────────────────

class ConfirmOcrRequest(BaseModel):
    structured_data: dict[str, Any]
    user_confirmed: bool

    @field_validator("user_confirmed")
    @classmethod
    def must_be_true(cls, v: bool) -> bool:
        if not v:
            raise ValueError("user_confirmed는 true여야 합니다.")
        return v


class ConfirmOcrResponse(BaseModel):
    document_id: int
    upload_status: UploadStatusEnum
    is_user_confirmed: bool
    confirmed_data: dict[str, Any] | None = None
    updated_at: datetime
