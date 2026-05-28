"""
약품, 복약, 활성도, 증상체크, 위험신호, 자가면역, 검사 모델
"""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from database import Base

# ── 약품 ──────────────────────────────────────────────────


class UserMedication(Base):
    """사용자 복용 약품 (API-약품-001~004)"""

    __tablename__ = "user_medications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    drug_name_user_input = Column(String(200), nullable=False)  # 사용자 입력 약품명
    drug_reference_id = Column(Integer, nullable=True)  # 약품 기준정보 ID (선택)
    dosage = Column(String(100), nullable=True)
    frequency = Column(String(100), nullable=True)
    duration_days = Column(Integer, nullable=True)
    is_autoimmune_drug = Column(Boolean, default=False, nullable=False)
    memo = Column(Text, nullable=True)

    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


# ── 복약 이력 ─────────────────────────────────────────────


class MedicationLog(Base):
    """복약 체크 이력 (API-복약-001/002)"""

    __tablename__ = "medication_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    medication_id = Column(Integer, ForeignKey("user_medications.id"), nullable=False, index=True)

    scheduled_date = Column(Date, nullable=False)
    scheduled_time = Column(String(5), nullable=True)  # HH:MM
    taken = Column(Boolean, nullable=True)  # NULL=미처리, True=복용, False=미복용
    taken_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


# ── 활성도 일지 ───────────────────────────────────────────


class ActivityLog(Base):
    """활성도 기록 (REQ-ACTV-001/002) — 일자당 1건 upsert"""

    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    log_date = Column(Date, nullable=False)
    pain_vas = Column(Integer, nullable=True)  # 통증 VAS 0~10
    fatigue = Column(Integer, nullable=True)  # 피로도 0~10
    morning_stiffness_minutes = Column(Integer, nullable=True)  # 아침 경직 (분)
    joint_swelling_areas = Column(Text, nullable=True)  # 관절 부종 부위 JSON
    daily_difficulty = Column(Integer, nullable=True)  # 일상 어려움 0~10
    free_memo = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "log_date", name="uq_activity_log_user_date"),)


# ── 증상 체크 ─────────────────────────────────────────────


class SymptomCheck(Base):
    """위험 증상 자가체크 (REQ-SYMP-001)"""

    __tablename__ = "symptom_checks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    checked_symptoms = Column(Text, nullable=False)  # JSON 배열
    safety_notice_required = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)


# ── 위험 신호 ─────────────────────────────────────────────


class RiskFlagStatusEnum(str, enum.Enum):
    active = "active"
    resolved = "resolved"
    dismissed = "dismissed"


class RiskFlag(Base):
    """위험 신호 (REQ-SYMP-002)"""

    __tablename__ = "risk_flags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    source_type = Column(String(50), nullable=False)  # symptom_check, activity_log 등
    source_id = Column(Integer, nullable=True)
    flag_type = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    consultation_recommended = Column(Boolean, default=True, nullable=False)
    status = Column(Enum(RiskFlagStatusEnum), default=RiskFlagStatusEnum.active, nullable=False)

    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


# ── 자가면역 프로필 ───────────────────────────────────────


class AutoimmuneProfile(Base):
    """자가면역 위험요인 프로필 (REQ-AUTO-001) — 유저당 1개"""

    __tablename__ = "autoimmune_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    risk_factors = Column(Text, nullable=True)  # JSON 배열
    pregnancy_status = Column(String(50), nullable=True)
    vaccination_history = Column(Text, nullable=True)  # JSON 배열

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


# ── 진료 일정 ─────────────────────────────────────────────


class CareScheduleTypeEnum(str, enum.Enum):
    checkup = "checkup"  # 검사
    visit = "visit"  # 진료
    injection = "injection"  # 주사
    other = "other"


class CareSchedule(Base):
    """진료·검사·주사 일정 (REQ-AUTO-004)"""

    __tablename__ = "care_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    schedule_type = Column(Enum(CareScheduleTypeEnum), nullable=False)
    title = Column(String(200), nullable=False)
    scheduled_date = Column(Date, nullable=False)
    reminder_days_before = Column(Integer, default=1, nullable=False)
    memo = Column(Text, nullable=True)

    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


# ── 검사 결과 ─────────────────────────────────────────────


class LabResult(Base):
    """검사 결과 사용자 기록 (REQ-LAB-001)"""

    __tablename__ = "lab_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("medical_documents.id"), nullable=True)

    test_date = Column(Date, nullable=False)
    test_type = Column(String(200), nullable=False)
    user_recorded_value = Column(String(200), nullable=False)
    reference_range = Column(String(200), nullable=True)
    unit = Column(String(50), nullable=True)
    memo = Column(Text, nullable=True)

    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
