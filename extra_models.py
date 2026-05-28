"""
약품 기준정보, 활성도 임계 알림, 피드백, 보호자 공유 모델
"""
import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from database import Base

# ── 약품 기준정보 (식약처) ────────────────────────────────

class DrugReference(Base):
    """약품 기준 정보 (API-약품-007) — 식약처 데이터 기반"""
    __tablename__ = "drug_references"

    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_name = Column(String(300), nullable=False, index=True)
    ingredient = Column(Text, nullable=True)        # 주성분
    manufacturer = Column(String(200), nullable=True)
    source = Column(String(100), nullable=False, default="식약처 의약품안전나라")
    memo = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


# ── 활성도 임계 알림 ──────────────────────────────────────

class ActivityThreshold(Base):
    """활성도 알림 기준값 (API-활성도-003/004) — 사용자 자가 설정"""
    __tablename__ = "activity_thresholds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # metric_type: pain_vas, fatigue, morning_stiffness_minutes, daily_difficulty
    metric_type = Column(String(100), nullable=False)
    threshold_value = Column(Float, nullable=False)
    custom_message = Column(String(500), nullable=True)  # 사용자가 직접 작성한 메시지
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "metric_type", name="uq_activity_threshold_user_metric"),
    )


# ── 피드백 ────────────────────────────────────────────────

class FeedbackTargetTypeEnum(str, enum.Enum):
    guide = "guide"
    chat_message = "chat_message"
    ocr_result = "ocr_result"
    other = "other"


class Feedback(Base):
    """구조화 피드백 (API-피드백-001) — 가명처리 후 모델 개선 활용"""
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    target_type = Column(Enum(FeedbackTargetTypeEnum), nullable=False)
    target_id = Column(Integer, nullable=True)
    score = Column(Integer, nullable=False)          # 1~5
    comment = Column(String(1000), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)


# ── 보호자 공유 ───────────────────────────────────────────

class GuardianShare(Base):
    """보호자 공유 링크 (API-보호자-001~004)"""
    __tablename__ = "guardian_shares"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    guardian_name = Column(String(100), nullable=False)
    guardian_contact = Column(String(20), nullable=False)  # 휴대폰 번호
    share_categories = Column(Text, nullable=False)        # JSON: ["medical_records", "guides"]
    secure_link_token = Column(String(100), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)

    is_revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    # 감사 로그
    last_accessed_at = Column(DateTime, nullable=True)
    access_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
