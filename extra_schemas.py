from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, field_validator

from extra_models import FeedbackTargetTypeEnum

# 허용 metric_type
VALID_METRIC_TYPES = {"pain_vas", "fatigue", "morning_stiffness_minutes", "daily_difficulty"}
# 허용 share_categories
VALID_SHARE_CATEGORIES = {"medical_records", "guides", "lab_results", "activity_logs"}


# ── 약품 기준정보 ─────────────────────────────────────────

class DrugReferenceResponse(BaseModel):
    id: int
    drug_name: str
    ingredient: str | None = None
    manufacturer: str | None = None
    source: str

    class Config:
        from_attributes = True


# ── 활성도 임계 알림 ──────────────────────────────────────

class ActivityThresholdUpsert(BaseModel):
    metric_type: str
    threshold_value: float
    custom_message: str | None = None
    is_active: bool = True

    @field_validator("metric_type")
    @classmethod
    def metric_type_valid(cls, v):
        if v not in VALID_METRIC_TYPES:
            raise ValueError(f"metric_type은 {VALID_METRIC_TYPES} 중 하나여야 합니다.")
        return v

    @field_validator("threshold_value")
    @classmethod
    def threshold_range(cls, v):
        if v < 0:
            raise ValueError("기준값은 0 이상이어야 합니다.")
        if v > 10000:
            raise ValueError("기준값이 너무 큽니다.")
        return v

    @field_validator("custom_message")
    @classmethod
    def message_length(cls, v):
        if v and len(v) > 500:
            raise ValueError("메시지는 500자 이하여야 합니다.")
        return v


class ActivityThresholdResponse(BaseModel):
    id: int
    metric_type: str
    threshold_value: float
    custom_message: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── 피드백 ────────────────────────────────────────────────

class FeedbackCreate(BaseModel):
    target_type: FeedbackTargetTypeEnum
    target_id: int | None = None
    score: int
    comment: str | None = None

    @field_validator("score")
    @classmethod
    def score_range(cls, v):
        if not (1 <= v <= 5):
            raise ValueError("평점은 1~5 사이여야 합니다.")
        return v

    @field_validator("comment")
    @classmethod
    def comment_length(cls, v):
        if v and len(v) > 1000:
            raise ValueError("코멘트는 1000자 이하여야 합니다.")
        return v


class FeedbackResponse(BaseModel):
    id: int
    target_type: FeedbackTargetTypeEnum
    target_id: int | None = None
    score: int
    comment: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── 보호자 공유 ───────────────────────────────────────────

import json
import re

PHONE_REGEX = re.compile(r'^01[0-9]-?\d{3,4}-?\d{4}$')


class GuardianShareCreate(BaseModel):
    guardian_name: str
    guardian_contact: str
    share_categories: list[str]
    expires_at: datetime

    @field_validator("guardian_name")
    @classmethod
    def name_valid(cls, v):
        s = v.strip()
        if not s:
            raise ValueError("보호자 이름을 입력해주세요.")
        if len(s) > 100:
            raise ValueError("이름은 100자 이하여야 합니다.")
        return s

    @field_validator("guardian_contact")
    @classmethod
    def contact_valid(cls, v):
        if not PHONE_REGEX.match(v):
            raise ValueError("올바른 휴대폰 번호 형식이 아닙니다.")
        return v

    @field_validator("share_categories")
    @classmethod
    def categories_valid(cls, v):
        if not v:
            raise ValueError("공유 항목을 1개 이상 선택해주세요.")
        invalid = set(v) - VALID_SHARE_CATEGORIES
        if invalid:
            raise ValueError(f"올바르지 않은 공유 항목입니다: {invalid}")
        return list(set(v))

    @field_validator("expires_at")
    @classmethod
    def expires_future(cls, v):
        now = datetime.now(UTC)
        expires = v if v.tzinfo else v.replace(tzinfo=UTC)
        if expires <= now:
            raise ValueError("만료일은 현재 시각 이후여야 합니다.")
        return v


class GuardianShareResponse(BaseModel):
    id: int
    guardian_name: str
    guardian_contact: str
    share_categories: list[str]
    secure_link_token: str
    expires_at: datetime
    is_revoked: bool
    access_count: int
    created_at: datetime

    @classmethod
    def from_orm(cls, obj) -> "GuardianShareResponse":
        try:
            cats = json.loads(obj.share_categories)
            cats = cats if isinstance(cats, list) else []
        except (json.JSONDecodeError, TypeError, ValueError):
            cats = []
        return cls(
            id=obj.id,
            guardian_name=obj.guardian_name,
            guardian_contact=obj.guardian_contact,
            share_categories=cats,
            secure_link_token=obj.secure_link_token,
            expires_at=obj.expires_at,
            is_revoked=obj.is_revoked,
            access_count=obj.access_count,
            created_at=obj.created_at,
        )


class GuardianViewResponse(BaseModel):
    guardian_name: str
    share_categories: list[str]
    content: dict[str, Any]
    expires_at: datetime
