import enum

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from database import Base

# ── 동의 이력 ─────────────────────────────────────────────

class ConsentTypeEnum(str, enum.Enum):
    terms = "terms"                          # 서비스 이용약관
    privacy = "privacy"                      # 개인정보 처리방침
    sensitive_medical = "sensitive_medical"  # 민감 의료정보 처리
    marketing = "marketing"                  # 마케팅 수신
    location = "location"                    # 위치정보 수집
    guardian_share = "guardian_share"        # 보호자 공유


class UserConsent(Base):
    """동의 이력 (REQ-USER-001, API-사용자-004/005)"""
    __tablename__ = "user_consents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    consent_type = Column(Enum(ConsentTypeEnum), nullable=False)
    agreed = Column(Boolean, nullable=False)
    version = Column(String(20), nullable=False, default="1.0")  # 약관 버전
    agreed_at = Column(DateTime, nullable=True)   # 동의 시각 (철회 시 NULL)
    revoked_at = Column(DateTime, nullable=True)  # 철회 시각

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


# ── 모드 관리 ─────────────────────────────────────────────

class UserModeEnum(str, enum.Enum):
    general = "general"           # 일반 모드
    autoimmune = "autoimmune"     # 자가면역 모드


class UserMode(Base):
    """사용자 모드 설정 (REQ-MODE-001/002) — 유저당 1개"""
    __tablename__ = "user_modes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    mode = Column(Enum(UserModeEnum), nullable=False, default=UserModeEnum.general)
    selected_at = Column(DateTime, server_default=func.now(), nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


# ── 질환 관리 ─────────────────────────────────────────────

class UserDisease(Base):
    """사용자 질환 정보 (REQ-DISE-001/002)"""
    __tablename__ = "user_diseases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    disease_name = Column(String(200), nullable=False)       # 질환명 (사용자 입력)
    disease_code = Column(String(50), nullable=True)         # 질환 코드 (선택, 사용자 입력)
    diagnosis_date = Column(Date, nullable=True)             # 진단일 (선택)
    memo = Column(Text, nullable=True)                       # 메모 (선택)

    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
