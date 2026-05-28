"""
Post-MVP 모델
- 건강수치 (혈압·혈당)
- 일반 모드 증상 일기 / 복약 체크
- 콘텐츠 변환 (카드뉴스, TTS)
- 게임 (점수, 뱃지)
- 관리자 안전 필터 로그
"""
import enum

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from database import Base

# ── 건강수치 ─────────────────────────────────────────────

class HealthMetricTypeEnum(str, enum.Enum):
    blood_pressure_systolic = "blood_pressure_systolic"    # 수축기 혈압
    blood_pressure_diastolic = "blood_pressure_diastolic"  # 이완기 혈압
    blood_glucose_fasting = "blood_glucose_fasting"        # 공복 혈당
    blood_glucose_postprandial = "blood_glucose_postprandial"  # 식후 혈당
    heart_rate = "heart_rate"                              # 심박수
    weight = "weight"                                      # 체중
    other = "other"


class HealthMetric(Base):
    """건강 수치 수동 입력 (API-건강수치-001/002)"""
    __tablename__ = "health_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    metric_type = Column(Enum(HealthMetricTypeEnum), nullable=False)
    user_recorded_value = Column(Float, nullable=False)  # 사용자 기록값 (자동 판정 X)
    unit = Column(String(20), nullable=True)
    measured_at = Column(DateTime, nullable=False)       # 측정 시각 (사용자 입력)
    memo = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)


# ── 일반 모드 일기 ────────────────────────────────────────

class DiarySymptomLog(Base):
    """일반 모드 증상 일기 (API-일반-일기-001/002) — 복약과 완전 분리"""
    __tablename__ = "diary_symptom_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    log_date = Column(Date, nullable=False)
    overall_condition = Column(String(50), nullable=True)  # 예: good, fair, poor
    body_parts = Column(Text, nullable=True)               # JSON 배열
    feeling = Column(String(50), nullable=True)            # 감정 상태
    memo = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "log_date", name="uq_diary_symptom_user_date"),
    )


class DiaryMedicationLog(Base):
    """일반 모드 복약 체크 (API-일반-일기-003) — 증상과 완전 분리"""
    __tablename__ = "diary_medication_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    medication_id = Column(Integer, ForeignKey("user_medications.id"), nullable=False, index=True)

    log_date = Column(Date, nullable=False)
    time_slot = Column(String(20), nullable=True)  # 예: morning, afternoon, evening
    taken = Column(Boolean, nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)


# ── 콘텐츠 변환 ───────────────────────────────────────────

class ContentTypeEnum(str, enum.Enum):
    card_news = "card_news"
    tts = "tts"


class ContentStatusEnum(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class ContentSourceTypeEnum(str, enum.Enum):
    guide = "guide"
    report = "report"


class ContentConversion(Base):
    """콘텐츠 변환 이력 (API-콘텐츠-001/002/003)"""
    __tablename__ = "content_conversions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    content_type = Column(Enum(ContentTypeEnum), nullable=False)
    source_type = Column(Enum(ContentSourceTypeEnum), nullable=False)
    source_id = Column(Integer, nullable=False)
    voice_type = Column(String(50), nullable=True)   # TTS 전용

    status = Column(Enum(ContentStatusEnum), default=ContentStatusEnum.pending, nullable=False)
    file_path = Column(String(500), nullable=True)    # 생성된 파일 경로
    file_size = Column(Integer, nullable=True)
    error_message = Column(String(500), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


# ── 게임 ──────────────────────────────────────────────────

class GameTypeEnum(str, enum.Enum):
    medication_quiz = "medication_quiz"
    health_knowledge = "health_knowledge"
    other = "other"


class GameScore(Base):
    """미니게임 점수 기록 (API-게임-001)"""
    __tablename__ = "game_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    game_type = Column(Enum(GameTypeEnum), nullable=False)
    score = Column(Integer, nullable=False)
    points_earned = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class UserBadge(Base):
    """사용자 뱃지 (API-게임-002)"""
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    badge_type = Column(String(100), nullable=False)
    badge_name = Column(String(200), nullable=False)
    earned_at = Column(DateTime, server_default=func.now(), nullable=False)


class UserPoints(Base):
    """사용자 포인트 누적 (API-게임-002) — 유저당 1개"""
    __tablename__ = "user_points"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    total_points = Column(Integer, default=0, nullable=False)

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


# ── 관리자 안전 필터 로그 ─────────────────────────────────

class SafetyFilterLog(Base):
    """안전 필터 차단 이력 (API-관리자-001) — 의료행위 오해 표현 차단"""
    __tablename__ = "safety_filter_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    target_type = Column(String(50), nullable=False)    # guide, chat_message 등
    target_id = Column(Integer, nullable=True)
    blocked_reason = Column(String(200), nullable=False)
    filter_stage = Column(String(100), nullable=True)   # pre_generation, post_generation 등
    raw_content = Column(Text, nullable=True)           # 차단된 원본 내용 (가명처리)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
