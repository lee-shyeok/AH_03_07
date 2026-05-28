from __future__ import annotations

from pydantic import BaseModel, Field


class PreConsultationReportRequest(BaseModel):
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
