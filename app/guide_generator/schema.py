from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class GuideStatus(str, Enum):
    GENERATED = "GENERATED"
    BLOCKED_HIGH_RISK = "BLOCKED_HIGH_RISK"
    GENERATION_FAILED = "GENERATION_FAILED"


class HealthGuideInput(BaseModel):
    """AUTO-005(Phase 3)가 전달하는 통합 입력 계약."""

    user_id: int
    disease_codes: list[str] = []                    # REQ-DISE-001: RA·SLE 등
    high_risk_flag: bool = False                     # REQ-AUTO-006 게이트 결과
    high_risk_matched_items: list[str] = []          # 매칭된 게이트 코드 목록

    # Phase 3(AUTO-005)에서 채워질 입력 소스 — 스키마만 선언
    risk_factor_summary: str | None = None           # AUTO-001
    medication_list: list[str] = []                  # AUTO-002
    activity_score_summary: str | None = None        # ACTV-001 최근 30일 요약
    risk_symptom_codes: list[str] = []               # SYMP-001
    upcoming_appointments: list[str] = []            # AUTO-004
    lab_results_summary: str | None = None           # LAB-001
    pregnancy_lactation_codes: list[str] = []        # AUTO-SAFE-001
    vaccine_infection_prevention: str | None = None  # AUTO-PREV-001


class SourceItem(BaseModel):
    title: str
    section: str | None
    page: int | None
    organization: str
    published_year: int
    score: float


class HealthGuideOutput(BaseModel):
    user_id: int
    status: GuideStatus
    medication_general: str
    side_effect_monitoring: list[str]
    lifestyle_info: str
    symptom_summary: str
    sources: list[SourceItem]
    disclaimer: str
    created_at: datetime
