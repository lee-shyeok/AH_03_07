import json
from datetime import UTC, date, datetime
from typing import Any

from pydantic import BaseModel, field_validator

from postmvp_models import (
    ContentSourceTypeEnum,
    ContentStatusEnum,
    ContentTypeEnum,
    GameTypeEnum,
    HealthMetricTypeEnum,
)

# 허용 overall_condition
VALID_CONDITIONS = {"good", "fair", "poor", "very_poor"}
# 허용 feeling
VALID_FEELINGS = {"happy", "neutral", "sad", "anxious", "tired", "other"}
# 허용 time_slot
VALID_TIME_SLOTS = {"morning", "afternoon", "evening", "night", "other"}
# 게임 점수당 포인트
POINTS_PER_SCORE = {
    "medication_quiz": 10,
    "health_knowledge": 15,
    "other": 5,
}
# 뱃지 조건 (점수 임계값)
BADGE_THRESHOLDS = {
    100: ("beginner", "건강 첫걸음"),
    500: ("intermediate", "건강 관리 중"),
    1000: ("advanced", "건강 마스터"),
}


# ── 건강수치 ─────────────────────────────────────────────

class HealthMetricCreate(BaseModel):
    metric_type: HealthMetricTypeEnum
    user_recorded_value: float
    unit: str | None = None
    measured_at: datetime
    memo: str | None = None

    @field_validator("user_recorded_value")
    @classmethod
    def value_positive(cls, v):
        if v < 0:
            raise ValueError("측정값은 0 이상이어야 합니다.")
        if v > 99999:
            raise ValueError("측정값이 너무 큽니다.")
        return v

    @field_validator("unit")
    @classmethod
    def unit_length(cls, v):
        if v and len(v) > 20:
            raise ValueError("단위는 20자 이하여야 합니다.")
        return v

    @field_validator("measured_at")
    @classmethod
    def measured_not_future(cls, v):
        now = datetime.now(UTC)
        measured = v if v.tzinfo else v.replace(tzinfo=UTC)
        if measured > now:
            raise ValueError("측정 시각은 현재 시각 이후일 수 없습니다.")
        return v

    @field_validator("memo")
    @classmethod
    def memo_length(cls, v):
        if v and len(v) > 500:
            raise ValueError("메모는 500자 이하여야 합니다.")
        return v


class HealthMetricResponse(BaseModel):
    id: int
    metric_type: HealthMetricTypeEnum
    user_recorded_value: float
    unit: str | None = None
    measured_at: datetime
    memo: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── 일반 모드 일기 ────────────────────────────────────────

class DiarySymptomLogCreate(BaseModel):
    log_date: date
    overall_condition: str | None = None
    body_parts: list[str] | None = None
    feeling: str | None = None
    memo: str | None = None

    @field_validator("log_date")
    @classmethod
    def log_date_not_future(cls, v):
        if v > date.today():
            raise ValueError("기록일은 오늘 이후 날짜를 입력할 수 없습니다.")
        return v

    @field_validator("overall_condition")
    @classmethod
    def condition_valid(cls, v):
        if v is not None and v not in VALID_CONDITIONS:
            raise ValueError(f"overall_condition은 {VALID_CONDITIONS} 중 하나여야 합니다.")
        return v

    @field_validator("feeling")
    @classmethod
    def feeling_valid(cls, v):
        if v is not None and v not in VALID_FEELINGS:
            raise ValueError(f"feeling은 {VALID_FEELINGS} 중 하나여야 합니다.")
        return v

    @field_validator("body_parts")
    @classmethod
    def body_parts_valid(cls, v):
        if v is not None:
            if len(v) > 20:
                raise ValueError("body_parts는 최대 20개까지 입력할 수 있습니다.")
            for part in v:
                if len(part) > 50:
                    raise ValueError("각 부위 이름은 50자 이하여야 합니다.")
        return v

    @field_validator("memo")
    @classmethod
    def memo_length(cls, v):
        if v and len(v) > 2000:
            raise ValueError("메모는 2000자 이하여야 합니다.")
        return v


class DiarySymptomLogResponse(BaseModel):
    id: int
    log_date: date
    overall_condition: str | None = None
    body_parts: list[str] | None = None
    feeling: str | None = None
    memo: str | None = None
    created_at: datetime

    @classmethod
    def from_orm(cls, obj) -> "DiarySymptomLogResponse":
        parts = None
        if obj.body_parts:
            try:
                result = json.loads(obj.body_parts)
                parts = result if isinstance(result, list) else None
            except (json.JSONDecodeError, TypeError, ValueError):
                parts = None
        return cls(
            id=obj.id,
            log_date=obj.log_date,
            overall_condition=obj.overall_condition,
            body_parts=parts,
            feeling=obj.feeling,
            memo=obj.memo,
            created_at=obj.created_at,
        )


class DiaryMedicationLogCreate(BaseModel):
    log_date: date
    medication_id: int
    time_slot: str | None = None
    taken: bool

    @field_validator("log_date")
    @classmethod
    def log_date_not_future(cls, v):
        if v > date.today():
            raise ValueError("기록일은 오늘 이후 날짜를 입력할 수 없습니다.")
        return v

    @field_validator("time_slot")
    @classmethod
    def time_slot_valid(cls, v):
        if v is not None and v not in VALID_TIME_SLOTS:
            raise ValueError(f"time_slot은 {VALID_TIME_SLOTS} 중 하나여야 합니다.")
        return v


class DiaryMedicationLogResponse(BaseModel):
    id: int
    medication_id: int
    log_date: date
    time_slot: str | None = None
    taken: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── 일정 통합 캘린더 ──────────────────────────────────────

class ScheduleResponse(BaseModel):
    medications: list[dict[str, Any]]           # 복약 알림 일정
    prescriptions_end: list[dict[str, Any]]     # 처방 종료 예정일
    care_schedules: list[dict[str, Any]]        # 진료·검사 일정


# ── 콘텐츠 변환 ───────────────────────────────────────────

class CardNewsCreateRequest(BaseModel):
    source_id: int
    source_type: ContentSourceTypeEnum


class TTSCreateRequest(BaseModel):
    source_id: int
    source_type: ContentSourceTypeEnum
    voice_type: str | None = "standard"

    @field_validator("voice_type")
    @classmethod
    def voice_type_valid(cls, v):
        allowed = {"standard", "friendly", "calm"}
        if v not in allowed:
            raise ValueError(f"voice_type은 {allowed} 중 하나여야 합니다.")
        return v


class ContentConversionResponse(BaseModel):
    id: int
    content_type: ContentTypeEnum
    source_type: ContentSourceTypeEnum
    source_id: int
    status: ContentStatusEnum
    file_path: str | None = None
    file_size: int | None = None
    error_message: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── 게임 ──────────────────────────────────────────────────

class GameScoreCreate(BaseModel):
    game_type: GameTypeEnum
    score: int

    @field_validator("score")
    @classmethod
    def score_valid(cls, v):
        if v < 0:
            raise ValueError("점수는 0 이상이어야 합니다.")
        if v > 100000:
            raise ValueError("점수가 너무 큽니다.")
        return v


class GameScoreResponse(BaseModel):
    id: int
    game_type: GameTypeEnum
    score: int
    points_earned: int
    created_at: datetime

    class Config:
        from_attributes = True


class BadgeInfo(BaseModel):
    badge_type: str
    badge_name: str
    earned_at: datetime

    class Config:
        from_attributes = True


class UserBadgesResponse(BaseModel):
    total_points: int
    badges: list[BadgeInfo]


# ── 관리자 안전 필터 로그 ─────────────────────────────────

class SafetyFilterLogResponse(BaseModel):
    id: int
    target_type: str
    target_id: int | None = None
    blocked_reason: str
    filter_stage: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
