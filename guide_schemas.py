from datetime import datetime

from pydantic import BaseModel, field_validator

# ── 가이드 생성 요청 ──────────────────────────────────────


class GuideCreateRequest(BaseModel):
    record_id: int


# ── 가이드 재생성 요청 ────────────────────────────────────

VALID_REGEN_REASONS = {"내용이 부족함", "이해하기 어려움", "기타"}


class GuideRegenerateRequest(BaseModel):
    reason: str | None = None

    @field_validator("reason")
    @classmethod
    def reason_valid(cls, v):
        if v is not None and v not in VALID_REGEN_REASONS:
            raise ValueError(f"재생성 사유는 {VALID_REGEN_REASONS} 중 하나여야 합니다.")
        return v


# ── 가이드 응답 ───────────────────────────────────────────


class GuideBrief(BaseModel):
    """목록 조회용"""

    id: int
    record_id: int
    diagnosis: str  # 연관 진료 기록 진단명
    summary: str  # 가이드 요약 (앞 100자)
    status: str
    version: int
    created_at: datetime


class GuideDetail(BaseModel):
    """상세 조회"""

    id: int
    record_id: int
    diagnosis: str
    status: str
    version: int
    medication_guide: str | None = None
    lifestyle_guide: str | None = None
    precautions: str | None = None
    recommended_checkups: str | None = None
    disclaimer: str  # 면책 문구 — 항상 포함
    regeneration_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class GuideListResponse(BaseModel):
    items: list[GuideBrief]
    total: int
    page: int
    size: int


# ── 피드백 ────────────────────────────────────────────────


class GuideFeedbackRequest(BaseModel):
    accuracy: int
    clarity: int
    usefulness: int
    comment: str | None = None

    @field_validator("accuracy", "clarity", "usefulness")
    @classmethod
    def score_range(cls, v):
        if not (1 <= v <= 5):
            raise ValueError("평점은 1~5 사이여야 합니다.")
        return v

    @field_validator("comment")
    @classmethod
    def comment_length(cls, v):
        if v and len(v) > 500:
            raise ValueError("코멘트는 500자 이하여야 합니다.")
        return v


class GuideFeedbackResponse(BaseModel):
    id: int
    guide_id: int
    accuracy: int
    clarity: int
    usefulness: int
    comment: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
