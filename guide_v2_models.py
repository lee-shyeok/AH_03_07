"""
안내문(자가면역 포함) + 출처 + 섹션 + 생성 작업 + 약품 인식 + 리포트 모델
"""

import enum

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from database import Base

# ── 안내문 생성 작업 ──────────────────────────────────────


class GuideJobStatusEnum(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    high_risk_gate_blocked = "high_risk_gate_blocked"
    safety_filter_blocked = "safety_filter_blocked"


class GuideTypeEnum(str, enum.Enum):
    general = "general"
    autoimmune = "autoimmune"


class GuideTriggerTypeEnum(str, enum.Enum):
    manual = "manual"
    scheduled = "scheduled"


class GuideGenerationJob(Base):
    """안내문 생성 비동기 작업 (API-안내문-001/002)"""

    __tablename__ = "guide_generation_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    trigger_type = Column(Enum(GuideTriggerTypeEnum), nullable=False)
    guide_type = Column(Enum(GuideTypeEnum), nullable=False, default=GuideTypeEnum.general)
    status = Column(Enum(GuideJobStatusEnum), default=GuideJobStatusEnum.pending, nullable=False)

    # 완료 시 생성된 안내문 ID
    guide_id = Column(Integer, nullable=True)

    blocked_reason = Column(String(200), nullable=True)
    error_message = Column(String(500), nullable=True)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


# ── 안내문 출처 ───────────────────────────────────────────


class GuideSource(Base):
    """안내문 출처 (API-안내문-005) — 근거 추적성 보장"""

    __tablename__ = "guide_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guide_id = Column(Integer, ForeignKey("guides.id"), nullable=False, index=True)

    source_org = Column(String(200), nullable=True)
    source_title = Column(String(500), nullable=True)
    source_url = Column(String(1000), nullable=True)
    source_page = Column(String(50), nullable=True)
    used_for_section = Column(String(100), nullable=True)
    citation_order = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)


# ── 안내문 섹션 ───────────────────────────────────────────


class GuideSectionTypeEnum(str, enum.Enum):
    medication = "medication"
    lifestyle = "lifestyle"
    caution = "caution"
    autoimmune = "autoimmune"
    source_notice = "source_notice"


class GuideSection(Base):
    """안내문 섹션 (API-안내문-006)"""

    __tablename__ = "guide_sections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guide_id = Column(Integer, ForeignKey("guides.id"), nullable=False, index=True)

    section_type = Column(Enum(GuideSectionTypeEnum), nullable=False)
    section_title = Column(String(200), nullable=True)
    section_content = Column(Text, nullable=False)
    display_order = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)


# ── 약품 이미지 인식 ──────────────────────────────────────


class PillRecognition(Base):
    """약품 이미지 인식 이력 (API-약품-005/006)"""

    __tablename__ = "pill_recognitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    image_path = Column(String(500), nullable=False)  # 저장된 이미지 경로
    stored_filename = Column(String(100), nullable=False)  # UUID 기반 파일명
    candidates = Column(Text, nullable=True)  # JSON: [{drug_name, confidence}]
    confirmed_drug_name = Column(String(200), nullable=True)  # 사용자 확정 약품명
    user_confirmed = Column(Boolean, default=False, nullable=False)

    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


# ── 리포트 ────────────────────────────────────────────────


class ReportStatusEnum(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Report(Base):
    """진료 전 요약 리포트 (API-리포트-001~003)"""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    visit_date = Column(Date, nullable=False)
    status = Column(Enum(ReportStatusEnum), default=ReportStatusEnum.pending, nullable=False)
    content = Column(Text, nullable=True)  # 생성된 리포트 내용
    error_message = Column(String(500), nullable=True)

    # 공유 링크
    secure_link_token = Column(String(100), nullable=True, unique=True, index=True)
    share_expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
