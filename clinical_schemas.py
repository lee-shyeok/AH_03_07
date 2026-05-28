import json
from datetime import date, datetime

from pydantic import BaseModel, field_validator

from clinical_models import (
    CareScheduleTypeEnum,
    RiskFlagStatusEnum,
)

# ── 약품 ──────────────────────────────────────────────────

class UserMedicationCreate(BaseModel):
    drug_name_user_input: str
    drug_reference_id: int | None = None
    dosage: str | None = None
    frequency: str | None = None
    duration_days: int | None = None
    is_autoimmune_drug: bool = False
    memo: str | None = None

    @field_validator("drug_name_user_input")
    @classmethod
    def name_valid(cls, v):
        s = v.strip()
        if not s:
            raise ValueError("약품명을 입력해주세요.")
        if len(s) > 200:
            raise ValueError("약품명은 200자 이하여야 합니다.")
        return s

    @field_validator("duration_days")
    @classmethod
    def duration_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("복용 일수는 1 이상이어야 합니다.")
        return v

    @field_validator("memo")
    @classmethod
    def memo_length(cls, v):
        if v and len(v) > 1000:
            raise ValueError("메모는 1000자 이하여야 합니다.")
        return v


class UserMedicationUpdate(BaseModel):
    drug_name_user_input: str | None = None
    dosage: str | None = None
    frequency: str | None = None
    duration_days: int | None = None
    is_autoimmune_drug: bool | None = None
    memo: str | None = None

    @field_validator("drug_name_user_input")
    @classmethod
    def name_valid(cls, v):
        if v is not None:
            s = v.strip()
            if not s:
                raise ValueError("약품명을 입력해주세요.")
            if len(s) > 200:
                raise ValueError("약품명은 200자 이하여야 합니다.")
            return s
        return v

    @field_validator("duration_days")
    @classmethod
    def duration_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("복용 일수는 1 이상이어야 합니다.")
        return v

    @field_validator("memo")
    @classmethod
    def memo_length(cls, v):
        if v and len(v) > 1000:
            raise ValueError("메모는 1000자 이하여야 합니다.")
        return v


class UserMedicationResponse(BaseModel):
    id: int
    drug_name_user_input: str
    drug_reference_id: int | None = None
    dosage: str | None = None
    frequency: str | None = None
    duration_days: int | None = None
    is_autoimmune_drug: bool
    memo: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── 복약 이력 ─────────────────────────────────────────────

class MedicationLogCheckRequest(BaseModel):
    taken: bool


class MedicationLogResponse(BaseModel):
    id: int
    medication_id: int
    scheduled_date: date
    scheduled_time: str | None = None
    taken: bool | None = None
    taken_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── 활성도 일지 ───────────────────────────────────────────

class ActivityLogUpsert(BaseModel):
    log_date: date
    pain_vas: int | None = None
    fatigue: int | None = None
    morning_stiffness_minutes: int | None = None
    joint_swelling_areas: list[str] | None = None
    daily_difficulty: int | None = None
    free_memo: str | None = None

    @field_validator("log_date")
    @classmethod
    def log_date_not_future(cls, v):
        if v > date.today():
            raise ValueError("기록일은 오늘 이후 날짜를 입력할 수 없습니다.")
        return v

    @field_validator("pain_vas", "fatigue", "daily_difficulty")
    @classmethod
    def score_range(cls, v):
        if v is not None and not (0 <= v <= 10):
            raise ValueError("점수는 0~10 사이여야 합니다.")
        return v

    @field_validator("morning_stiffness_minutes")
    @classmethod
    def stiffness_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError("아침 경직 시간은 0 이상이어야 합니다.")
        return v

    @field_validator("free_memo")
    @classmethod
    def memo_length(cls, v):
        if v and len(v) > 2000:
            raise ValueError("메모는 2000자 이하여야 합니다.")
        return v


class ActivityLogResponse(BaseModel):
    id: int
    log_date: date
    pain_vas: int | None = None
    fatigue: int | None = None
    morning_stiffness_minutes: int | None = None
    joint_swelling_areas: list[str] | None = None
    daily_difficulty: int | None = None
    free_memo: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm(cls, obj) -> "ActivityLogResponse":
        areas = None
        if obj.joint_swelling_areas:
            try:
                result = json.loads(obj.joint_swelling_areas)
                areas = result if isinstance(result, list) else None
            except (json.JSONDecodeError, TypeError, ValueError):
                areas = None
        return cls(
            id=obj.id,
            log_date=obj.log_date,
            pain_vas=obj.pain_vas,
            fatigue=obj.fatigue,
            morning_stiffness_minutes=obj.morning_stiffness_minutes,
            joint_swelling_areas=areas,
            daily_difficulty=obj.daily_difficulty,
            free_memo=obj.free_memo,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )


# ── 증상 체크 ─────────────────────────────────────────────

# 안전 체크 트리거 증상 키워드
SAFETY_NOTICE_SYMPTOMS = {
    "고열", "호흡곤란", "흉통", "실신", "의식저하",
    "심한 관절 부종", "갑작스러운 시야 저하",
}

class SymptomCheckCreate(BaseModel):
    checked_symptoms: list[str]

    @field_validator("checked_symptoms")
    @classmethod
    def symptoms_valid(cls, v):
        if not v:
            raise ValueError("증상을 1개 이상 선택해주세요.")
        if len(v) > 50:
            raise ValueError("증상은 최대 50개까지 선택할 수 있습니다.")
        for s in v:
            if len(s) > 100:
                raise ValueError("증상명은 100자 이하여야 합니다.")
        return v


class SymptomCheckResponse(BaseModel):
    id: int
    checked_symptoms: list[str]
    safety_notice_required: bool
    created_at: datetime

    @classmethod
    def from_orm(cls, obj) -> "SymptomCheckResponse":
        try:
            symptoms = json.loads(obj.checked_symptoms)
            symptoms = symptoms if isinstance(symptoms, list) else []
        except (json.JSONDecodeError, TypeError, ValueError):
            symptoms = []
        return cls(
            id=obj.id,
            checked_symptoms=symptoms,
            safety_notice_required=obj.safety_notice_required,
            created_at=obj.created_at,
        )


# ── 위험 신호 ─────────────────────────────────────────────

class RiskFlagUpdateRequest(BaseModel):
    status: RiskFlagStatusEnum

    @field_validator("status")
    @classmethod
    def status_not_active(cls, v):
        if v == RiskFlagStatusEnum.active:
            raise ValueError("active로 변경할 수 없습니다. resolved 또는 dismissed만 가능합니다.")
        return v


class RiskFlagResponse(BaseModel):
    id: int
    source_type: str
    source_id: int | None = None
    flag_type: str
    message: str
    consultation_recommended: bool
    status: RiskFlagStatusEnum
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── 자가면역 프로필 ───────────────────────────────────────

class AutoimmuneProfileUpdate(BaseModel):
    risk_factors: list[str] | None = None
    pregnancy_status: str | None = None
    vaccination_history: list[str] | None = None

    @field_validator("pregnancy_status")
    @classmethod
    def pregnancy_valid(cls, v):
        if v is not None:
            allowed = {"none", "pregnant", "breastfeeding", "planning"}
            if v not in allowed:
                raise ValueError(f"pregnancy_status는 {allowed} 중 하나여야 합니다.")
        return v

    @field_validator("risk_factors", "vaccination_history")
    @classmethod
    def list_length(cls, v):
        if v is not None and len(v) > 50:
            raise ValueError("항목은 최대 50개까지 입력할 수 있습니다.")
        return v


class AutoimmuneProfileResponse(BaseModel):
    risk_factors: list[str] | None = None
    pregnancy_status: str | None = None
    vaccination_history: list[str] | None = None
    updated_at: datetime

    @classmethod
    def from_orm(cls, obj) -> "AutoimmuneProfileResponse":
        def safe_list(val):
            if not val:
                return None
            try:
                r = json.loads(val)
                return r if isinstance(r, list) else None
            except (json.JSONDecodeError, TypeError, ValueError):
                return None

        return cls(
            risk_factors=safe_list(obj.risk_factors),
            pregnancy_status=obj.pregnancy_status,
            vaccination_history=safe_list(obj.vaccination_history),
            updated_at=obj.updated_at,
        )


# ── 진료 일정 ─────────────────────────────────────────────

class CareScheduleCreate(BaseModel):
    schedule_type: CareScheduleTypeEnum
    title: str
    scheduled_date: date
    reminder_days_before: int = 1
    memo: str | None = None

    @field_validator("title")
    @classmethod
    def title_valid(cls, v):
        s = v.strip()
        if not s:
            raise ValueError("일정 제목을 입력해주세요.")
        if len(s) > 200:
            raise ValueError("제목은 200자 이하여야 합니다.")
        return s

    @field_validator("reminder_days_before")
    @classmethod
    def reminder_range(cls, v):
        if not (0 <= v <= 30):
            raise ValueError("알림은 0~30일 전 사이로 설정할 수 있습니다.")
        return v

    @field_validator("memo")
    @classmethod
    def memo_length(cls, v):
        if v and len(v) > 1000:
            raise ValueError("메모는 1000자 이하여야 합니다.")
        return v


class CareScheduleUpdate(BaseModel):
    schedule_type: CareScheduleTypeEnum | None = None
    title: str | None = None
    scheduled_date: date | None = None
    reminder_days_before: int | None = None
    memo: str | None = None

    @field_validator("title")
    @classmethod
    def title_valid(cls, v):
        if v is not None:
            s = v.strip()
            if not s:
                raise ValueError("일정 제목을 입력해주세요.")
            if len(s) > 200:
                raise ValueError("제목은 200자 이하여야 합니다.")
            return s
        return v

    @field_validator("reminder_days_before")
    @classmethod
    def reminder_range(cls, v):
        if v is not None and not (0 <= v <= 30):
            raise ValueError("알림은 0~30일 전 사이로 설정할 수 있습니다.")
        return v

    @field_validator("memo")
    @classmethod
    def memo_length(cls, v):
        if v and len(v) > 1000:
            raise ValueError("메모는 1000자 이하여야 합니다.")
        return v


class CareScheduleResponse(BaseModel):
    id: int
    schedule_type: CareScheduleTypeEnum
    title: str
    scheduled_date: date
    reminder_days_before: int
    memo: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── 검사 결과 ─────────────────────────────────────────────

class LabResultCreate(BaseModel):
    test_date: date
    test_type: str
    user_recorded_value: str
    reference_range: str | None = None
    unit: str | None = None
    document_id: int | None = None
    memo: str | None = None

    @field_validator("test_date")
    @classmethod
    def test_date_not_future(cls, v):
        if v > date.today():
            raise ValueError("검사일은 오늘 이후 날짜를 입력할 수 없습니다.")
        return v

    @field_validator("test_type")
    @classmethod
    def test_type_valid(cls, v):
        s = v.strip()
        if not s:
            raise ValueError("검사 유형을 입력해주세요.")
        if len(s) > 200:
            raise ValueError("검사 유형은 200자 이하여야 합니다.")
        return s

    @field_validator("user_recorded_value")
    @classmethod
    def value_valid(cls, v):
        s = v.strip()
        if not s:
            raise ValueError("검사값을 입력해주세요.")
        if len(s) > 200:
            raise ValueError("검사값은 200자 이하여야 합니다.")
        return s

    @field_validator("memo")
    @classmethod
    def memo_length(cls, v):
        if v and len(v) > 1000:
            raise ValueError("메모는 1000자 이하여야 합니다.")
        return v


class LabResultResponse(BaseModel):
    id: int
    test_date: date
    test_type: str
    user_recorded_value: str
    reference_range: str | None = None
    unit: str | None = None
    document_id: int | None = None
    memo: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
