import json
import re
from datetime import date, datetime

from pydantic import BaseModel, field_validator, model_validator

VALID_WEEKDAYS = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
TIME_REGEX = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")
VALID_CHANNELS = {"app", "email", "kakao"}


# ── 복약 알림 설정 ─────────────────────────────────────────


class MedicationReminderCreate(BaseModel):
    drug_name: str
    medication_id: int | None = None
    remind_times: list[str]
    start_date: date
    end_date: date | None = None
    weekdays: list[str]
    channels: list[str]

    @field_validator("drug_name")
    @classmethod
    def drug_name_valid(cls, v):
        stripped = v.strip()
        if not stripped:
            raise ValueError("약품명을 입력해주세요.")
        if len(stripped) > 200:
            raise ValueError("약품명은 200자 이하여야 합니다.")
        return stripped

    @field_validator("start_date")
    @classmethod
    def start_date_not_past(cls, v):
        if v < date.today():
            raise ValueError("시작일은 오늘 이후여야 합니다.")
        return v

    @field_validator("remind_times")
    @classmethod
    def remind_times_valid(cls, v):
        if not v:
            raise ValueError("알림 시각을 1개 이상 입력해주세요.")
        if len(v) > 10:
            raise ValueError("알림 시각은 최대 10개까지 설정할 수 있습니다.")
        for t in v:
            if not TIME_REGEX.match(t):
                raise ValueError(f"알림 시각 형식이 올바르지 않습니다: {t} (예: 08:00)")
        return list(dict.fromkeys(v))

    @field_validator("weekdays")
    @classmethod
    def weekdays_valid(cls, v):
        if not v:
            raise ValueError("요일을 1개 이상 선택해주세요.")
        invalid = set(v) - VALID_WEEKDAYS
        if invalid:
            raise ValueError(f"올바르지 않은 요일입니다: {invalid}")
        return list(set(v))

    @field_validator("channels")
    @classmethod
    def channels_valid(cls, v):
        if not v:
            raise ValueError("알림 채널을 1개 이상 선택해주세요.")
        invalid = set(v) - VALID_CHANNELS
        if invalid:
            raise ValueError(f"올바르지 않은 채널입니다: {invalid}")
        return list(set(v))

    @model_validator(mode="after")
    def date_range_valid(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("종료일은 시작일 이후여야 합니다.")
        return self


class MedicationReminderUpdate(BaseModel):
    drug_name: str | None = None
    remind_times: list[str] | None = None
    start_date: date | None = None
    end_date: date | None = None
    weekdays: list[str] | None = None
    channels: list[str] | None = None
    is_active: bool | None = None

    @field_validator("drug_name")
    @classmethod
    def drug_name_valid(cls, v):
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("약품명을 입력해주세요.")
            if len(stripped) > 200:
                raise ValueError("약품명은 200자 이하여야 합니다.")
            return stripped
        return v

    # [수정 4] 수정 시에도 과거 날짜 차단
    @field_validator("start_date")
    @classmethod
    def start_date_not_past(cls, v):
        if v is not None and v < date.today():
            raise ValueError("시작일은 오늘 이후여야 합니다.")
        return v

    @field_validator("remind_times")
    @classmethod
    def remind_times_valid(cls, v):
        if v is not None:
            if not v:
                raise ValueError("알림 시각을 1개 이상 입력해주세요.")
            if len(v) > 10:
                raise ValueError("알림 시각은 최대 10개까지 설정할 수 있습니다.")
            for t in v:
                if not TIME_REGEX.match(t):
                    raise ValueError(f"알림 시각 형식이 올바르지 않습니다: {t} (예: 08:00)")
            return list(dict.fromkeys(v))
        return v

    @field_validator("weekdays")
    @classmethod
    def weekdays_valid(cls, v):
        if v is not None:
            if not v:
                raise ValueError("요일을 1개 이상 선택해주세요.")
            invalid = set(v) - VALID_WEEKDAYS
            if invalid:
                raise ValueError(f"올바르지 않은 요일입니다: {invalid}")
            return list(set(v))
        return v

    @field_validator("channels")
    @classmethod
    def channels_valid(cls, v):
        if v is not None:
            if not v:
                raise ValueError("알림 채널을 1개 이상 선택해주세요.")
            invalid = set(v) - VALID_CHANNELS
            if invalid:
                raise ValueError(f"올바르지 않은 채널입니다: {invalid}")
            return list(set(v))
        return v


class MedicationReminderResponse(BaseModel):
    id: int
    drug_name: str
    medication_id: int | None = None
    remind_times: list[str]
    start_date: date
    end_date: date | None = None
    weekdays: list[str]
    channels: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm(cls, obj) -> "MedicationReminderResponse":
        # [수정 2] JSON 파싱 실패 시 빈 리스트로 안전 처리
        def safe_loads(val: str, default: list) -> list:
            try:
                result = json.loads(val)
                return result if isinstance(result, list) else default
            except (json.JSONDecodeError, TypeError, ValueError):
                return default

        return cls(
            id=obj.id,
            drug_name=obj.drug_name,
            medication_id=obj.medication_id,
            remind_times=safe_loads(obj.remind_times, []),
            start_date=obj.start_date,
            end_date=obj.end_date,
            weekdays=safe_loads(obj.weekdays, []),
            channels=safe_loads(obj.channels, []),
            is_active=obj.is_active,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )


class MedicationReminderListResponse(BaseModel):
    items: list[MedicationReminderResponse]
    total: int


# ── 알림 목록 ─────────────────────────────────────────────


class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    title: str
    message: str
    backlink: str | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    size: int
    unread_count: int


# ── 알림 설정 ─────────────────────────────────────────────


class NotificationSettingUpdate(BaseModel):
    medication_enabled: bool | None = None
    guide_enabled: bool | None = None
    marketing_enabled: bool | None = None
    app_enabled: bool | None = None
    email_enabled: bool | None = None
    kakao_enabled: bool | None = None


class NotificationSettingResponse(BaseModel):
    medication_enabled: bool
    guide_enabled: bool
    marketing_enabled: bool
    app_enabled: bool
    email_enabled: bool
    kakao_enabled: bool
    updated_at: datetime

    class Config:
        from_attributes = True
