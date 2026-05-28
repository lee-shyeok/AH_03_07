import json
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, field_validator

from guide_v2_models import (
    GuideJobStatusEnum,
    GuideSectionTypeEnum,
    GuideTriggerTypeEnum,
    ReportStatusEnum,
)

# ── 안내문 생성 작업 ──────────────────────────────────────


class GuideGenerateRequest(BaseModel):
    trigger_type: GuideTriggerTypeEnum = GuideTriggerTypeEnum.manual


class GuideGenerationJobResponse(BaseModel):
    job_id: int
    status: GuideJobStatusEnum
    guide_id: int | None = None
    blocked_reason: str | None = None
    error_message: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj) -> "GuideGenerationJobResponse":
        return cls(
            job_id=obj.id,
            status=obj.status,
            guide_id=obj.guide_id,
            blocked_reason=obj.blocked_reason,
            error_message=obj.error_message,
            created_at=obj.created_at,
        )


# ── 안내문 출처 ───────────────────────────────────────────


class GuideSourceResponse(BaseModel):
    id: int
    source_org: str | None = None
    source_title: str | None = None
    source_url: str | None = None
    source_page: str | None = None
    used_for_section: str | None = None
    citation_order: int

    class Config:
        from_attributes = True


# ── 안내문 섹션 ───────────────────────────────────────────


class GuideSectionResponse(BaseModel):
    id: int
    section_type: GuideSectionTypeEnum
    section_title: str | None = None
    section_content: str
    display_order: int

    class Config:
        from_attributes = True


# ── 처방전 편의 응답 ──────────────────────────────────────


class PrescriptionBrief(BaseModel):
    id: int
    original_filename: str
    upload_status: str
    is_user_confirmed: bool
    confirmed_data: dict[str, Any] | None = None
    created_at: datetime

    @classmethod
    def from_orm(cls, doc) -> "PrescriptionBrief":
        confirmed = None
        if doc.confirmed_data:
            try:
                confirmed = json.loads(doc.confirmed_data)
            except (json.JSONDecodeError, TypeError, ValueError):
                confirmed = None
        return cls(
            id=doc.id,
            original_filename=doc.original_filename,
            upload_status=doc.upload_status.value,
            is_user_confirmed=doc.is_user_confirmed,
            confirmed_data=confirmed,
            created_at=doc.created_at,
        )


# ── 약품 이미지 인식 ──────────────────────────────────────


class PillCandidate(BaseModel):
    drug_name: str
    confidence: float


class PillRecognitionResponse(BaseModel):
    id: int
    candidates: list[PillCandidate]
    user_confirm_required: bool = True
    confirmed_drug_name: str | None = None
    user_confirmed: bool
    created_at: datetime

    @classmethod
    def from_orm(cls, obj) -> "PillRecognitionResponse":
        candidates = []
        if obj.candidates:
            try:
                raw = json.loads(obj.candidates)
                candidates = [PillCandidate(**c) for c in raw if isinstance(c, dict)]
            except (json.JSONDecodeError, TypeError, ValueError, KeyError):
                candidates = []
        return cls(
            id=obj.id,
            candidates=candidates,
            user_confirm_required=True,
            confirmed_drug_name=obj.confirmed_drug_name,
            user_confirmed=obj.user_confirmed,
            created_at=obj.created_at,
        )


# ── 리포트 ────────────────────────────────────────────────


class ReportCreateRequest(BaseModel):
    visit_date: date

    @field_validator("visit_date")
    @classmethod
    def visit_date_valid(cls, v):
        # 미래 진료 예약도 허용 (진료 전 요약이므로)
        return v


class ReportResponse(BaseModel):
    id: int
    visit_date: date
    status: ReportStatusEnum
    content: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportShareResponse(BaseModel):
    report_id: int
    secure_link_token: str
    share_expires_at: datetime
