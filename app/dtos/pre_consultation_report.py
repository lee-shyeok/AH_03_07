from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.pre_consultation_report import ReportStatus


class PreConsultationReportRequest(BaseModel):
    visit_date: date = Field(description="다음 진료 예정일")
    questions: list[str] | None = Field(
        default=None,
        description="의료진에게 묻고 싶은 질문 목록 (사용자 직접 입력)",
    )
    period_days: int = Field(
        default=30,
        ge=1,
        le=90,
        description="최근 며칠치 데이터 (기본 30, 최대 90)",
    )


class ReportCreatedResponse(BaseModel):  # POST /reports/pre-visit 202
    report_id: int
    status: ReportStatus


class ReportStatusResponse(BaseModel):  # GET /reports/{id} 002
    id: int
    status: ReportStatus
    visit_date: date
    created_at: datetime
    pdf_base64: str | None = None  # COMPLETED일 때만 채움


class ReportShareRequest(BaseModel):  # POST /reports/{id}/share 요청
    recipient_email: str


class ReportShareResponse(BaseModel):  # 003 응답 201
    secure_link_token: str
