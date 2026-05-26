from sqlalchemy import Column, Integer, String, Enum, Boolean, Date, DateTime, Text
from sqlalchemy.sql import func
from database import Base
import enum


class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 기본 정보 (REQ-USER-001)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(200), nullable=False)          # bcrypt 해시
    name = Column(String(100), nullable=False)
    birth_date = Column(Date, nullable=True)
    gender = Column(Enum(GenderEnum), nullable=True)
    phone_number = Column(String(20), nullable=True)
    profile_image_url = Column(String(500), nullable=True)

    # 의료 정보 (REQ-USER-007)
    chronic_diseases = Column(Text, nullable=True)          # JSON 배열 문자열
    allergy_info = Column(Text, nullable=True)              # 자유 입력

    # 이메일 인증 (REQ-USER-002)
    is_email_verified = Column(Boolean, default=False, nullable=False)

    # 약관 동의 (REQ-USER-001)
    agreed_terms = Column(Boolean, default=False, nullable=False)
    agreed_privacy = Column(Boolean, default=False, nullable=False)
    agreed_sensitive_medical = Column(Boolean, default=False, nullable=False)

    # 계정 상태
    is_active = Column(Boolean, default=True, nullable=False)

    # 탈퇴 Soft Delete (REQ-USER-008)
    deleted_at = Column(DateTime, nullable=True)
    # 소셜 로그인
    social_provider = Column(String(20), nullable=True)   # "google", "kakao", "naver"
    social_id = Column(String(200), nullable=True)        # 소셜 고유 ID
    withdrawal_reason = Column(String(500), nullable=True)

    # 타임스탬프
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
